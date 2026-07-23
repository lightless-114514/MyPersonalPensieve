"""时间胶囊 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
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
from app.services.upload_service import save_upload_file, get_file_full_path, IMAGE_MIME_TYPES
from app.models.capsule import CapsuleContentType, TimeCapsule, CapsuleStatus

router = APIRouter(prefix="/api/capsules", tags=["capsules"])


@router.post("", response_model=CapsuleResponse, status_code=201)
async def create_capsule(
    memory_id: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    title: str = Form(...),
    open_date: str = Form(...),
    message: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    """创建时间胶囊（支持文件上传）"""
    from datetime import datetime as dt

    try:
        # 解析 open_date
        parsed_date = dt.fromisoformat(open_date.replace("Z", "+00:00"))

        req = CapsuleCreateRequest(
            memory_id=memory_id,
            content=content,
            title=title,
            open_date=parsed_date,
            message=message,
        )

        file_path = None
        file_size = None
        mime_type = None

        # 处理文件上传
        if file:
            mime = file.content_type or "application/octet-stream"
            if mime not in IMAGE_MIME_TYPES:
                raise ValueError("仅支持上传图片文件（JPEG/PNG/GIF/WebP/BMP/SVG）")
            file_info = await save_upload_file(file, "CAPSULE")
            file_path = file_info["file_path"]
            file_size = file_info["file_size"]
            mime_type = file_info["mime_type"]

        return await capsule_service.create(db, req, file_path, file_size, mime_type)
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


@router.get("/{capsule_id}/file")
async def get_capsule_file(
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取胶囊关联的图片文件（inline 预览）"""
    capsule = await db.get(TimeCapsule, capsule_id)
    if not capsule:
        raise HTTPException(status_code=404, detail="胶囊不存在")
    if not capsule.file_path:
        raise HTTPException(status_code=404, detail="胶囊没有关联的文件")
    # 只有已开启的胶囊才能查看文件
    if capsule.status not in (CapsuleStatus.OPENED, CapsuleStatus.FORCED_OPEN):
        raise HTTPException(status_code=403, detail="胶囊尚未开启，无法查看文件")

    full_path = get_file_full_path(capsule.file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(full_path),
        media_type=capsule.mime_type or "application/octet-stream",
        filename=full_path.name,
        content_disposition_type="inline",
    )