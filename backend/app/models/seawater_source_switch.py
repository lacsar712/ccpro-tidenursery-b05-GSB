from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SeawaterSourceSwitch(Base):
    """海水源切换日志：每次切换水源必须留痕。"""

    __tablename__ = "seawater_source_switches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hatchery_id: Mapped[int] = mapped_column(
        ForeignKey("hatcheries.id"), nullable=False, index=True
    )
    switched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    old_source_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_source_summary: Mapped[str] = mapped_column(Text, nullable=False)
    operator_name: Mapped[str] = mapped_column(String(128), nullable=False)

    hatchery: Mapped["Hatchery"] = relationship(back_populates="source_switches")
