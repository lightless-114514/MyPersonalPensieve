from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from app.db.session import get_db
from app.schemas.memory import MemoryRequest, UpdateMemoryRequest, MemoryResponse, PagedResponse
from app.services.memory_service import memory_service
from app.services.redis_service import redis_service
from app.services.llm_service import llm_service
from fastapi import Header
from typing import Optional

async def get_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    llm_service.set_api_key(x_api_key)
    return x_api_key

router = APIRouter(prefix="/api/memories", tags=["memories"])


async def check_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    limited = await redis_service.is_rate_limited(ip)
    if limited:
        raise HTTPException(status_code=429, detail="Too many requests")


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(
    body: MemoryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    try:
        return await memory_service.create(db, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tags")
async def get_all_tags(
    q: str = Query(None, description="Search tags"),
    page: int = Query(0, ge=0, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select as sa_select
    from app.models.memory import MemoryTag

    # 构建基础子查询：获取去重后的标签
    base_subq = sa_select(MemoryTag.tag).group_by(MemoryTag.tag)
    if q:
        base_subq = base_subq.where(MemoryTag.tag.ilike(f"%{q}%"))

    # 总数查询
    count_stmt = sa_select(func.count()).select_from(base_subq.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 分页查询
    stmt = sa_select(MemoryTag.tag, func.count(MemoryTag.tag).label("count"))
    if q:
        stmt = stmt.where(MemoryTag.tag.ilike(f"%{q}%"))
    stmt = stmt.group_by(MemoryTag.tag).order_by(func.count(MemoryTag.tag).desc()).offset(page * size).limit(size)

    result = await db.execute(stmt)
    rows = result.all()
    items = [{"tag": row.tag, "count": row.count} for row in rows]
    total_pages = (total + size - 1) // size
    return {
        "content": items,
        "page": page,
        "size": size,
        "total_elements": total,
        "total_pages": total_pages,
    }


@router.get("", response_model=PagedResponse)
async def get_all_memories(
    request: Request,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    favorite: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    return await memory_service.get_all(db, page, size, favorite)


@router.get("/recent", response_model=list[MemoryResponse])
async def get_recent_memories(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    big_tag: Optional[str] = Query(None, description="按大标签过滤"),
    tags: Optional[str] = Query(None, description="按小标签过滤，逗号分隔"),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    return await memory_service.get_recent(db, limit, big_tag=big_tag, tags=tags)


@router.get("/{id}", response_model=MemoryResponse)
async def get_memory_by_id(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    try:
        return await memory_service.get_by_id(db, id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{id}", response_model=MemoryResponse)
async def update_memory(
    id: str,
    body: UpdateMemoryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    try:
        return await memory_service.update(db, id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{id}", status_code=204)
async def delete_memory(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    try:
        await memory_service.delete(db, id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
