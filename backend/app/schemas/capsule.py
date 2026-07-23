from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CapsuleCreateRequest(BaseModel):
    """创建时间胶囊请求（JSON 模式，不含文件上传）"""
    memory_id: Optional[str] = Field(None, description="关联的日记ID（从记忆库选取时必填）")
    content: Optional[str] = Field(None, description="胶囊自带内容（新建内容时必填）")
    title: str = Field(..., max_length=500, description="胶囊标题")
    open_date: datetime = Field(..., description="预定开启日期")
    message: Optional[str] = Field(None, description="给未来自己的一段话")


class CapsuleResponse(BaseModel):
    """时间胶囊响应 — 列表用，不包含日记内容"""
    id: str
    memory_id: Optional[str] = None
    content: Optional[str] = None
    title: str
    open_date: datetime
    buried_date: datetime
    status: str
    opened_at: Optional[datetime] = None
    is_forced: bool = False
    message: Optional[str] = None
    memory_title: Optional[str] = None  # 关联日记标题（仅预览）
    source_type: str = "memory"  # "memory" 或 "custom"
    content_type: Optional[str] = None  # "TEXT" 或 "IMAGE"
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CapsuleDetailResponse(CapsuleResponse):
    """时间胶囊详情 — 包含日记内容（仅开启后返回）"""
    memory_content: Optional[str] = None  # 日记内容（仅开启后可用）
    memory_type: Optional[str] = None


class CapsuleStatsResponse(BaseModel):
    """时间胶囊统计"""
    waiting_count: int = 0     # 等待开封
    opened_count: int = 0      # 已开启（含破拆）
    forced_count: int = 0      # 破拆数
    ready_count: int = 0       # 已到期可开封


class CapsulePagedResponse(BaseModel):
    """分页响应"""
    content: list[CapsuleResponse]
    page: int
    size: int
    total_elements: int
    total_pages: int
    last: bool
    first: bool