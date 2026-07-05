"""文件上传与下载路由。"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from app.db.session import get_db
from app.schemas.memory import MemoryResponse
from app.services.memory_service import memory_service
from app.services.upload_service import (
    save_upload_file, get_file_full_path, delete_file,
    IMAGE_MIME_TYPES, DOCUMENT_MIME_TYPES, TEXT_MIME_TYPES,
)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=MemoryResponse, status_code=201)
async def upload_memory_with_file(
    file: UploadFile = File(...),
    title: str = Form(""),
    content: str = Form(""),
    source_url: str = Form(""),
    tags: str = Form(""),
    big_tag: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """上传文件并创建记忆。根据 MIME 类型自动判断记忆类型 (IMAGE/FILE)。"""
    mime_type = file.content_type or "application/octet-stream"

    # 自动判断记忆类型
    if mime_type in IMAGE_MIME_TYPES:
        memory_type = "IMAGE"
    else:
        memory_type = "FILE"

    # 保存文件
    try:
        file_info = await save_upload_file(file, memory_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 如果没有提供标题，使用文件名
    if not title:
        title = file.filename or "未命名文件"

    # 如果没有提供内容，为文档类型自动生成描述
    if not content:
        if mime_type in IMAGE_MIME_TYPES:
            content = f"图片: {file.filename}"
        elif mime_type in DOCUMENT_MIME_TYPES:
            content = f"文档: {file.filename}"
        else:
            content = f"文件: {file.filename}"

    # 解析 tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    from app.schemas.memory import MemoryRequest
    request = MemoryRequest(
        title=title,
        content=content,
        type=memory_type,
        source_url=source_url or None,
        tags=tag_list,
        big_tag=big_tag or None,
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        mime_type=file_info["mime_type"],
    )

    try:
        return await memory_service.create(db, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{memory_id}/download")
async def download_file(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
):
    """下载/预览记忆关联的文件。"""
    try:
        memory = await memory_service.get_by_id(db, memory_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="记忆不存在")

    if not memory.file_path:
        raise HTTPException(status_code=404, detail="该记忆没有关联文件")

    full_path = get_file_full_path(memory.file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 根据文件类型决定是否 inline 显示
    media_types = IMAGE_MIME_TYPES | DOCUMENT_MIME_TYPES | TEXT_MIME_TYPES
    disposition = "inline" if memory.mime_type in media_types else "attachment"

    # inline 模式不设置 filename，避免浏览器将图片当作下载处理
    # attachment 模式设置 filename 以提供默认下载文件名
    if disposition == "inline":
        return FileResponse(
            path=str(full_path),
            media_type=memory.mime_type or "application/octet-stream",
            content_disposition_type="inline",
        )
    else:
        return FileResponse(
            path=str(full_path),
            media_type=memory.mime_type or "application/octet-stream",
            filename=full_path.name,
            content_disposition_type="attachment",
        )