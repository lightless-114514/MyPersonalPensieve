"""时间胶囊业务逻辑"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.capsule import TimeCapsule, CapsuleStatus
from app.models.memory import Memory
from app.schemas.capsule import (
    CapsuleCreateRequest,
    CapsuleResponse,
    CapsuleDetailResponse,
    CapsuleStatsResponse,
    CapsulePagedResponse,
)


class CapsuleService:
    """时间胶囊服务"""

    async def create(self, db: AsyncSession, req: CapsuleCreateRequest) -> CapsuleResponse:
        """创建时间胶囊"""
        # 验证关联日记存在
        memory = await db.get(Memory, req.memory_id)
        if not memory:
            raise ValueError("关联的日记不存在")

        # 验证开启日期在未来
        if req.open_date <= datetime.now():
            raise ValueError("开启日期必须在当前时间之后")

        capsule = TimeCapsule(
            memory_id=req.memory_id,
            title=req.title,
            open_date=req.open_date,
            message=req.message,
            status=CapsuleStatus.SEALED,
        )
        db.add(capsule)
        await db.commit()
        await db.refresh(capsule)

        return CapsuleResponse(
            id=capsule.id,
            memory_id=capsule.memory_id,
            title=capsule.title,
            open_date=capsule.open_date,
            buried_date=capsule.buried_date,
            status=capsule.status.value,
            opened_at=capsule.opened_at,
            is_forced=capsule.is_forced,
            message=capsule.message,
            memory_title=memory.title,
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
    ) -> CapsulePagedResponse:
        """获取胶囊列表（分页+搜索）"""
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
                title=c.title,
                open_date=c.open_date,
                buried_date=c.buried_date,
                status=c.status.value,
                opened_at=c.opened_at,
                is_forced=c.is_forced,
                message=c.message,
                memory_title=c.memory.title if c.memory else None,
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
        # 只有已开启的胶囊才返回日记内容
        if capsule.status in (CapsuleStatus.OPENED, CapsuleStatus.FORCED_OPEN):
            memory_content = capsule.memory.content if capsule.memory else None
            memory_type = capsule.memory.type.value if capsule.memory else None

        return CapsuleDetailResponse(
            id=capsule.id,
            memory_id=capsule.memory_id,
            title=capsule.title,
            open_date=capsule.open_date,
            buried_date=capsule.buried_date,
            status=capsule.status.value,
            opened_at=capsule.opened_at,
            is_forced=capsule.is_forced,
            message=capsule.message,
            memory_title=capsule.memory.title if capsule.memory else None,
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