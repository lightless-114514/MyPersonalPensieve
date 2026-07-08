from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# ---- 隐私状态 ----

class PrivacyStatusUpdate(BaseModel):
    """更新日记隐私状态"""
    privacy_status: str  # ANALYZE / STORE / LOCKED


# ---- 周报 / 月报生成请求 ----

class GenerateWeeklyRequest(BaseModel):
    """生成周报请求"""
    week_start: str  # YYYY-MM-DD，该周周一日期

class GenerateMonthlyRequest(BaseModel):
    """生成月报请求"""
    month_start: str  # YYYY-MM-DD，该月1号日期


# ---- 洞察报告响应 ----

class InsightReportResponse(BaseModel):
    id: str
    report_type: str       # WEEKLY / MONTHLY
    date_start: str
    date_end: str
    summary: str
    emotion_curve: str     # JSON string
    keywords: str          # JSON string
    low_point: str         # JSON string
    high_point: str        # JSON string
    pattern: str           # JSON string (月报专用)
    core_theme: str        # JSON string (月报专用)
    memory_count: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InsightReportListItem(BaseModel):
    """档案列表精简项"""
    id: str
    report_type: str
    date_start: str
    date_end: str
    summary: str
    memory_count: int
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WeeklyStatusResponse(BaseModel):
    """周报生成状态"""
    week_start: str
    exists: bool
    report_id: Optional[str] = None
    has_new_memories: bool = False  # 已有周报但该周有新日记


class InsightArchiveResponse(BaseModel):
    """洞察档案列表"""
    total: int
    items: list[InsightReportListItem]