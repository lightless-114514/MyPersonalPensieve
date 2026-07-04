from pydantic import BaseModel, Field
from typing import Optional


class CompareRequest(BaseModel):
    """记忆对比请求"""
    source_ids: list[str] = Field(..., description="源记忆ID列表（左侧/较早）")
    target_ids: list[str] = Field(..., description="目标记忆ID列表（右侧/较晚）")


class ComparePoint(BaseModel):
    """单个对比点"""
    content: str = Field(..., description="对比内容描述")
    source_refs: Optional[list[str]] = Field(default=None, description="关联的源记忆标题")
    target_refs: Optional[list[str]] = Field(default=None, description="关联的目标记忆标题")


class CompareResult(BaseModel):
    """对比结果"""
    similarities: list[ComparePoint] = Field(default_factory=list, description="相同点")
    differences: list[ComparePoint] = Field(default_factory=list, description="变化点")
    source_summary: str = Field(default="", description="源记忆概要")
    target_summary: str = Field(default="", description="目标记忆概要")
    time_span_days: Optional[int] = Field(default=None, description="时间跨度（天）")
    earliest_date: Optional[str] = Field(default=None, description="最早记忆日期")
    latest_date: Optional[str] = Field(default=None, description="最晚记忆日期")
    source_count: int = Field(default=0, description="源记忆数量")
    target_count: int = Field(default=0, description="目标记忆数量")
    source_tags: list[str] = Field(default_factory=list, description="源记忆标签")
    target_tags: list[str] = Field(default_factory=list, description="目标记忆标签")
    growth_insight: Optional[str] = Field(default=None, description="成长洞察")