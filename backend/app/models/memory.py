import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, Float, DateTime, ForeignKey, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base
import enum


class MemoryType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    LINK = "LINK"


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


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[MemoryType] = mapped_column(SAEnum(MemoryType), nullable=False, default=MemoryType.TEXT)
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sentiment: Mapped[Sentiment | None] = mapped_column(SAEnum(Sentiment), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SAEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

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
