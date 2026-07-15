"""时间胶囊 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.capsule import (
    CapsuleCreateRequest,
    CapsuleResponse,
    CapsuleDetailResponse,
    CapsuleStatsResponse,
    CapsulePagedResponse,
)
from app.services.capsule_service import capsule_service

router = APIRouter(prefix="/api/capsules", tags=["capsules"])


@router.post("", response_model=CapsuleResponse, status_code=201)
async def create_capsule(
    body: CapsuleCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建时间胶囊"""
    try:
        return await capsule_service.create(db, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats", response_model=CapsuleStatsResponse)
async def get_capsule_stats(db: AsyncSession = Depends(get_db)):
    """获取胶囊统计信息"""
    return await capsule_service.get_stats(db)


@router.get("/check-ready")
async def check_ready_capsules(db: AsyncSession = Depends(get_db)):
    """检查是否有到期的胶囊（用于首页通知）"""
    return await capsule_service.check_ready(db)


@router.get("", response_model=CapsulePagedResponse)
async def get_capsules(
    page: int = Query(0, ge=0),
    size: int = Query(5, ge=1, le=50),
    status: Optional[str] = Query(None, description="按状态过滤: SEALED / OPENED / FORCED_OPEN"),
    search: Optional[str] = Query(None, description="搜索标题或留言"),
    db: AsyncSession = Depends(get_db),
):
    """获取胶囊列表（分页+搜索）"""
    return await capsule_service.get_all(db, page, size, status, search)


@router.get("/{capsule_id}", response_model=CapsuleDetailResponse)
async def get_capsule_detail(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取胶囊详情（封存状态不返回日记内容）"""
    try:
        return await capsule_service.get_by_id(db, capsule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{capsule_id}/open", response_model=CapsuleDetailResponse)
async def open_capsule(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """正常开启胶囊（到期后）"""
    try:
        return await capsule_service.open_capsule(db, capsule_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{capsule_id}/force-open", response_model=CapsuleDetailResponse)
async def force_open_capsule(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """强行破拆胶囊"""
    try:
        return await capsule_service.force_open(db, capsule_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{capsule_id}", status_code=204)
async def delete_capsule(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除胶囊"""
    try:
        await capsule_service.delete(db, capsule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))