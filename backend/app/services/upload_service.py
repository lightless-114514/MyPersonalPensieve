"""文件上传服务 — 将文件保存到 uploads 目录，返回相对路径。"""
import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import settings

# 允许的 MIME 类型
ALLOWED_MIME_TYPES = {
    # 图片
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml",
    # 文档
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    # 文本
    "text/plain", "text/markdown", "text/csv",
    "application/json",
    "text/html",
}

# 按类型分组
IMAGE_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml",
}

DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

TEXT_MIME_TYPES = {
    "text/plain", "text/markdown", "text/csv", "application/json", "text/html",
}

# 文件大小限制（字节）
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB
MAX_FILE_SIZE = 20 * 1024 * 1024    # 20MB


def _upload_dir() -> Path:
    """获取上传目录，不存在则创建。"""
    d = Path(settings.upload_dir_resolved)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _guess_extension(filename: str, mime_type: str) -> str:
    """根据文件名和 MIME 类型推断扩展名。"""
    if filename:
        ext = Path(filename).suffix
        if ext:
            return ext
    # 常见 MIME 到扩展名映射
    mime_to_ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "text/csv": ".csv",
        "application/json": ".json",
        "text/html": ".html",
    }
    return mime_to_ext.get(mime_type, ".bin")


async def save_upload_file(file: UploadFile, memory_type: str = "FILE") -> dict:
    """
    保存上传文件到 uploads 目录。
    返回 {"file_path": 相对路径, "file_size": 字节数, "mime_type": MIME类型}
    """
    content = await file.read()
    file_size = len(content)

    # 校验大小
    max_size = MAX_IMAGE_SIZE if memory_type == "IMAGE" else MAX_FILE_SIZE
    if file_size > max_size:
        raise ValueError(f"文件大小超过限制（最大 {max_size // 1024 // 1024}MB）")

    mime_type = file.content_type or "application/octet-stream"

    # 校验 MIME 类型
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"不支持的文件类型: {mime_type}")

    # 生成唯一文件名
    ext = _guess_extension(file.filename or "", mime_type)
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # 按日期子目录组织: uploads/YYYY-MM/
    from datetime import datetime
    date_dir = datetime.now().strftime("%Y-%m")
    save_dir = _upload_dir() / date_dir
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / unique_name
    with open(save_path, "wb") as f:
        f.write(content)

    # 返回相对路径（相对于 upload_dir）
    rel_path = f"{date_dir}/{unique_name}"
    return {
        "file_path": rel_path,
        "file_size": file_size,
        "mime_type": mime_type,
    }


def get_file_full_path(relative_path: str) -> Path:
    """根据相对路径获取文件的完整路径。"""
    return _upload_dir() / relative_path


def delete_file(relative_path: str) -> bool:
    """删除上传的文件。"""
    full_path = get_file_full_path(relative_path)
    if full_path.exists():
        full_path.unlink()
        return True
    return False