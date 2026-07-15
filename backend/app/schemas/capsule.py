from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CapsuleCreateRequest(BaseModel):
    """创建时间胶囊请求"""
    memory_id: str = Field(..., description="关联的日记ID")
    title: str = Field(..., max_length=500, description="胶囊标题")
    open_date: datetime = Field(..., description="预定开启日期")
    message: Optional[str] = Field(None, description="给未来自己的一段话")


class CapsuleResponse(BaseModel):
    """时间胶囊响应 — 列表用，不包含日记内容"""
    id: str
    memory_id: str
    title: str
    open_date: datetime
    buried_date: datetime
    status: str
    opened_at: Optional[datetime] = None
    is_forced: bool = False
    message: Optional[str] = None
    memory_title: Optional[str] = None  # 关联日记标题（仅预览）
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