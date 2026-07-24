"""时间胶囊业务逻辑"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.capsule import TimeCapsule, CapsuleStatus, CapsuleContentType
from app.models.memory import Memory, BigTag
from app.schemas.capsule import (
    CapsuleCreateRequest,
    CapsuleResponse,
    CapsuleDetailResponse,
    CapsuleStatsResponse,
    CapsulePagedResponse,
)


def _ensure_naive(dt: datetime) -> datetime:
    """将时区感知的datetime转换为naive datetime（去掉时区信息），
    避免与 datetime.now() 比较时抛出 TypeError。
    前端可能发送带Z后缀的ISO时间字符串（如 2026-07-19T00:00:00.000Z），
    Pydantic会将其解析为时区感知datetime，而 datetime.now() 是naive的，
    两者无法直接比较。"""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


class CapsuleService:
    """时间胶囊服务"""

    async def create(
        self,
        db: AsyncSession,
        req: CapsuleCreateRequest,
        file_path: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> CapsuleResponse:
        """创建时间胶囊"""
        # 验证：必须提供 memory_id 或 content 之一
        if not req.memory_id and not req.content and not file_path:
            raise ValueError("必须选择一篇记忆、输入内容或上传图片")
        if req.memory_id and (req.content or file_path):
            raise ValueError("不能同时选择记忆和输入/上传内容")

        memory_title = None
        source_type = "custom"
        content_type = CapsuleContentType.TEXT.value
        big_tag = None

        # 如果从记忆库选取，验证记忆存在
        if req.memory_id:
            memory = await db.get(Memory, req.memory_id)
            if not memory:
                raise ValueError("关联的日记不存在")
            memory_title = memory.title
            source_type = "memory"
            big_tag = memory.big_tag.value if memory.big_tag else None
        elif file_path:
            # 图片类型胶囊
            content_type = CapsuleContentType.IMAGE.value

        # 将时区感知datetime转为naive，确保与 datetime.now() 兼容比较
        open_date = _ensure_naive(req.open_date)

        # 验证开启日期在未来
        if open_date <= datetime.now():
            raise ValueError("开启日期必须在当前时间之后")

        capsule = TimeCapsule(
            memory_id=req.memory_id,
            content=req.content if not req.memory_id else None,
            title=req.title,
            open_date=open_date,
            message=req.message,
            status=CapsuleStatus.SEALED,
            content_type=content_type,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
        )
        db.add(capsule)
        await db.commit()
        await db.refresh(capsule)

        return CapsuleResponse(
            id=capsule.id,
            memory_id=capsule.memory_id,
            content=capsule.content,
            title=capsule.title,
            open_date=capsule.open_date,
            buried_date=capsule.buried_date,
            status=capsule.status.value,
            opened_at=capsule.opened_at,
            is_forced=capsule.is_forced,
            message=capsule.message,
            memory_title=memory_title,
            source_type=source_type,
            content_type=capsule.content_type,
            file_path=capsule.file_path,
            file_size=capsule.file_size,
            mime_type=capsule.mime_type,
            big_tag=big_tag,  # 从关联记忆获取
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
        )

    async def get_stats(self, db: AsyncSession) -> CapsuleStatsResponse:
        """获取胶囊统计"""
        now = datetime.now()

        waiting_count = await db.scalar(
            select(func.count(TimeCapsule.id)).where(TimeCapsule.status == CapsuleStatus.SEALED)
        )
        opened_count = await db.scalar(
            select(func.count(TimeCapsule.id)).where(
                TimeCapsule.status.in_([CapsuleStatus.OPENED, CapsuleStatus.FORCED_OPEN])
            )
        )
        forced_count = await db.scalar(
            select(func.count(TimeCapsule.id)).where(TimeCapsule.status == CapsuleStatus.FORCED_OPEN)
        )
        ready_count = await db.scalar(
            select(func.count(TimeCapsule.id)).where(
                and_(TimeCapsule.status == CapsuleStatus.SEALED, TimeCapsule.open_date <= now)
            )
        )

        return CapsuleStatsResponse(
            waiting_count=waiting_count or 0,
            opened_count=opened_count or 0,
            forced_count=forced_count or 0,
            ready_count=ready_count or 0,
        )

    async def get_all(
        self,
        db: AsyncSession,
        page: int = 0,
        size: int = 5,
        status: str | None = None,
        search: str | None = None,
        big_tag: str | None = None,
    ) -> CapsulePagedResponse:
        """获取胶囊列表（分页+搜索+大标签筛选）"""
        query = select(TimeCapsule).options(selectinload(TimeCapsule.memory))

        if status:
            query = query.where(TimeCapsule.status == CapsuleStatus(status))
        if search:
            query = query.where(
                or_(
                    TimeCapsule.title.ilike(f"%{search}%"),
                    TimeCapsule.message.ilike(f"%{search}%"),
                )
            )
        if big_tag:
            query = query.where(
                TimeCapsule.memory_id.isnot(None)
            ).join(
                Memory, TimeCapsule.memory_id == Memory.id
            ).where(
                Memory.big_tag == BigTag(big_tag)
            )

        # 总数
        count_query = select(func.count(TimeCapsule.id))
        if status:
            count_query = count_query.where(TimeCapsule.status == CapsuleStatus(status))
        if search:
            count_query = count_query.where(
                or_(
                    TimeCapsule.title.ilike(f"%{search}%"),
                    TimeCapsule.message.ilike(f"%{search}%"),
                )
            )
        if big_tag:
            count_query = count_query.where(
                TimeCapsule.memory_id.isnot(None)
            ).join(
                Memory, TimeCapsule.memory_id == Memory.id
            ).where(
                Memory.big_tag == BigTag(big_tag)
            )
        total = await db.scalar(count_query) or 0

        # 分页
        query = query.order_by(TimeCapsule.created_at.desc()).offset(page * size).limit(size)
        result = await db.execute(query)
        capsules = result.scalars().all()

        items = []
        for c in capsules:
            items.append(CapsuleResponse(
                id=c.id,
                memory_id=c.memory_id,
                content=c.content,
                title=c.title,
                open_date=c.open_date,
                buried_date=c.buried_date,
                status=c.status.value,
                opened_at=c.opened_at,
                is_forced=c.is_forced,
                message=c.message,
                memory_title=c.memory.title if c.memory else None,
                source_type="memory" if c.memory_id else "custom",
                content_type=c.content_type,
                file_path=c.file_path,
                file_size=c.file_size,
                mime_type=c.mime_type,
                big_tag=c.memory.big_tag.value if c.memory and c.memory.big_tag else None,
                created_at=c.created_at,
                updated_at=c.updated_at,
            ))

        total_pages = (total + size - 1) // size
        return CapsulePagedResponse(
            content=items,
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
            last=page >= total_pages - 1,
            first=page == 0,
        )

    async def get_by_id(self, db: AsyncSession, capsule_id: str) -> CapsuleDetailResponse:
        """获取胶囊详情"""
        capsule = await db.get(TimeCapsule, capsule_id, options=[selectinload(TimeCapsule.memory)])
        if not capsule:
            raise ValueError("胶囊不存在")

        memory_content = None
        memory_type = None
        # 只有已开启的胶囊才返回内容
        if capsule.status in (CapsuleStatus.OPENED, CapsuleStatus.FORCED_OPEN):
            if capsule.memory:
                memory_content = capsule.memory.content
                memory_type = capsule.memory.type.value
            elif capsule.content_type == CapsuleContentType.IMAGE.value:
                # 图片类型胶囊 — 返回标记
                memory_content = "[图片]"
                memory_type = "IMAGE"
            elif capsule.content:
                # 文字类型自定义胶囊
                memory_content = capsule.content
                memory_type = "TEXT"

        return CapsuleDetailResponse(
            id=capsule.id,
            memory_id=capsule.memory_id,
            content=capsule.content,
            title=capsule.title,
            open_date=capsule.open_date,
            buried_date=capsule.buried_date,
            status=capsule.status.value,
            opened_at=capsule.opened_at,
            is_forced=capsule.is_forced,
            message=capsule.message,
            memory_title=capsule.memory.title if capsule.memory else None,
            source_type="memory" if capsule.memory_id else "custom",
            content_type=capsule.content_type,
            file_path=capsule.file_path,
            file_size=capsule.file_size,
            mime_type=capsule.mime_type,
            big_tag=capsule.memory.big_tag.value if capsule.memory and capsule.memory.big_tag else None,
            memory_content=memory_content,
            memory_type=memory_type,
            created_at=capsule.created_at,
            updated_at=capsule.updated_at,
        )

    async def open_capsule(self, db: AsyncSession, capsule_id: str) -> CapsuleDetailResponse:
        """正常开启胶囊（到达指定日期后）"""
        capsule = await db.get(TimeCapsule, capsule_id, options=[selectinload(TimeCapsule.memory)])
        if not capsule:
            raise ValueError("胶囊不存在")

        if capsule.status != CapsuleStatus.SEALED:
            raise ValueError("胶囊已经开启过了")

        now = datetime.now()
        if capsule.open_date > now:
            raise ValueError("胶囊尚未到期，无法开启")

        capsule.status = CapsuleStatus.OPENED
        capsule.opened_at = now
        capsule.is_forced = False
        await db.commit()
        await db.refresh(capsule)

        return await self.get_by_id(db, capsule_id)

    async def force_open(self, db: AsyncSession, capsule_id: str) -> CapsuleDetailResponse:
        """强行破拆胶囊"""
        capsule = await db.get(TimeCapsule, capsule_id, options=[selectinload(TimeCapsule.memory)])
        if not capsule:
            raise ValueError("胶囊不存在")

        if capsule.status != CapsuleStatus.SEALED:
            raise ValueError("胶囊已经开启过了")

        capsule.status = CapsuleStatus.FORCED_OPEN
        capsule.opened_at = datetime.now()
        capsule.is_forced = True
        await db.commit()
        await db.refresh(capsule)

        return await self.get_by_id(db, capsule_id)

    async def delete(self, db: AsyncSession, capsule_id: str) -> None:
        """删除胶囊"""
        capsule = await db.get(TimeCapsule, capsule_id)
        if not capsule:
            raise ValueError("胶囊不存在")
        await db.delete(capsule)
        await db.commit()

    async def check_ready(self, db: AsyncSession) -> list[dict]:
        """检查是否有到期的胶囊（用于首页通知）"""
        now = datetime.now()
        stmt = (
            select(TimeCapsule)
            .where(and_(TimeCapsule.status == CapsuleStatus.SEALED, TimeCapsule.open_date <= now))
            .order_by(TimeCapsule.open_date.asc())
        )
        result = await db.execute(stmt)
        capsules = result.scalars().all()

        return [
            {
                "id": c.id,
                "title": c.title,
                "open_date": c.open_date.isoformat(),
                "buried_date": c.buried_date.isoformat(),
            }
            for c in capsules
        ]


capsule_service = CapsuleService()