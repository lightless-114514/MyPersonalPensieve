from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from app.db.session import get_db
from app.schemas.memory import MemoryRequest, MemoryResponse, PagedResponse
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
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


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
    q: str = Query(None, description="搜索标签关键词"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """返回所有不重复的标签，支持搜索过滤。按使用次数降序排列。"""
    from sqlalchemy import select as sa_select
    from app.models.memory import MemoryTag

    stmt = sa_select(MemoryTag.tag, func.count(MemoryTag.tag).label("count"))
    if q:
        stmt = stmt.where(MemoryTag.tag.ilike(f"%{q}%"))
    stmt = stmt.group_by(MemoryTag.tag).order_by(func.count(MemoryTag.tag).desc()).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()
    return [{"tag": row.tag, "count": row.count} for row in rows]


@router.get("", response_model=PagedResponse)
async def get_all_memories(
    request: Request,
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    return await memory_service.get_all(db, page, size)


@router.get("/recent", response_model=list[MemoryResponse])
async def get_recent_memories(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await check_rate_limit(request)
    return await memory_service.get_recent(db, limit)


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