from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 海水源切换后的水质样水源确认窗口长度
SOURCE_CONFIRM_WINDOW_HOURS = 24


class SourceSwitchLog(Base):
    """海水源切换日志：每次切换必须留痕，并在场字段上同事务更新。"""

    __tablename__ = "source_switch_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hatchery_id: Mapped[int] = mapped_column(
        ForeignKey("hatcheries.id"), nullable=False, index=True
    )
    switched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    old_source_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_source_summary: Mapped[str] = mapped_column(Text, nullable=False)
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False)

    hatchery: Mapped["Hatchery"] = relationship("Hatchery", back_populates="source_switch_logs")
