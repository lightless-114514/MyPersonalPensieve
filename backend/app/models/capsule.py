import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    String, Text, DateTime, ForeignKey, Enum as SAEnum, Boolean, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base


class CapsuleStatus(str, enum.Enum):
    """时间胶囊状态"""
    SEALED = "SEALED"          # 已封存，等待开启日期
    OPENED = "OPENED"          # 已正常开启
    FORCED_OPEN = "FORCED_OPEN"  # 强行破拆


class TimeCapsule(Base):
    """时间胶囊 — 将日记封存到未来某个日期"""
    __tablename__ = "time_capsules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    memory_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="胶囊标题")
    open_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="预定开启日期")
    buried_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, comment="埋藏日期"
    )
    status: Mapped[CapsuleStatus] = mapped_column(
        SAEnum(CapsuleStatus), nullable=False, default=CapsuleStatus.SEALED
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="实际开启时间")
    is_forced: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否强行破拆"
    )
    message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="给未来自己的一段话"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # 关联原始日记
    memory: Mapped["Memory"] = relationship("Memory")