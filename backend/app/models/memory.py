import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, Float, Integer, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum, Boolean
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base
import enum


class MemoryType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"


class Sentiment(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EntityType(str, enum.Enum):
    PERSON = "PERSON"
    PLACE = "PLACE"
    ORG = "ORG"
    EVENT = "EVENT"
    TOPIC = "TOPIC"
    TECHNOLOGY = "TECHNOLOGY"
    OTHER = "OTHER"


class BigTag(str, enum.Enum):
    """大标签 — 大的彩色分类标签，区别于普通小标签"""
    KNOWLEDGE_POINT = "KNOWLEDGE_POINT"    # 知识点
    FREEFORM_NOTE = "FREEFORM_NOTE"        # 随心记述
    INSPIRATION_FLASH = "INSPIRATION_FLASH"  # 灵感闪现
    DECISION_DILEMMA = "DECISION_DILEMMA"   # 决策纠结


class PrivacyStatus(str, enum.Enum):
    """日记隐私状态：纳入分析 / 仅存储 / 加密锁定"""
    ANALYZE = "ANALYZE"      # 纳入分析（默认）
    STORE = "STORE"          # 仅存储，AI 不可见
    LOCKED = "LOCKED"        # 加密锁定，需密码查看


class InsightType(str, enum.Enum):
    """洞察报告类型"""
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[MemoryType] = mapped_column(SAEnum(MemoryType), nullable=False, default=MemoryType.TEXT)
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Float, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sentiment: Mapped[Sentiment | None] = mapped_column(SAEnum(Sentiment), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SAEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING
    )
    big_tag: Mapped[BigTag | None] = mapped_column(SAEnum(BigTag), nullable=True)
    privacy_status: Mapped[PrivacyStatus] = mapped_column(
        SAEnum(PrivacyStatus), nullable=False, default=PrivacyStatus.ANALYZE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    tags: Mapped[list["MemoryTag"]] = relationship("MemoryTag", cascade="all, delete-orphan")
    memory_entities: Mapped[list["MemoryEntity"]] = relationship("MemoryEntity", back_populates="memory", cascade="all, delete-orphan")


class MemoryTag(Base):
    __tablename__ = "memory_tags"

    memory_id: Mapped[str] = mapped_column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)


class KnowledgeEntity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[EntityType] = mapped_column(SAEnum(EntityType), nullable=False)

    memory_entities: Mapped[list["MemoryEntity"]] = relationship("MemoryEntity", back_populates="entity", cascade="all, delete-orphan")


class MemoryEntity(Base):
    __tablename__ = "memory_entity"
    __table_args__ = (
        UniqueConstraint("memory_id", "entity_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    memory_id: Mapped[str] = mapped_column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)

    memory: Mapped["Memory"] = relationship("Memory", back_populates="memory_entities")
    entity: Mapped["KnowledgeEntity"] = relationship("KnowledgeEntity", back_populates="memory_entities")


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("entities.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("memories.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    source_entity: Mapped["KnowledgeEntity"] = relationship("KnowledgeEntity", foreign_keys=[source_entity_id])
    target_entity: Mapped["KnowledgeEntity"] = relationship("KnowledgeEntity", foreign_keys=[target_entity_id])
    memory: Mapped["Memory | None"] = relationship("Memory")


class InsightReport(Base):
    """洞察报告：周报 / 月报"""
    __tablename__ = "insight_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type: Mapped[InsightType] = mapped_column(SAEnum(InsightType), nullable=False)
    # 覆盖的日期范围
    date_start: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    date_end: Mapped[str] = mapped_column(String(10), nullable=False)    # YYYY-MM-DD
    # 报告内容（JSON 字符串）
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")         # 一句话总结
    emotion_curve: Mapped[str] = mapped_column(Text, nullable=False, default="")   # 情绪曲线数据 JSON
    keywords: Mapped[str] = mapped_column(Text, nullable=False, default="")        # 高频关键词 JSON
    low_point: Mapped[str] = mapped_column(Text, nullable=False, default="")       # 情绪低点摘要 JSON
    high_point: Mapped[str] = mapped_column(Text, nullable=False, default="")      # 情绪高点摘要 JSON
    pattern: Mapped[str] = mapped_column(Text, nullable=False, default="")         # 显著模式（月报专用）
    core_theme: Mapped[str] = mapped_column(Text, nullable=False, default="")      # 核心主题（月报专用）
    # 元数据
    memory_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 分析的日记数
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)   # 是否已读
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
