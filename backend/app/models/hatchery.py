from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.seawater_source_switch import SeawaterSourceSwitch

SOURCE_CONFIRMATION_WINDOW = timedelta(hours=24)


class Hatchery(Base):
    __tablename__ = "hatcheries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    seawater_source: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ponds: Mapped[List["Pond"]] = relationship(
        "Pond", back_populates="hatchery", cascade="all, delete-orphan"
    )
    source_switches: Mapped[List[SeawaterSourceSwitch]] = relationship(
        "SeawaterSourceSwitch",
        back_populates="hatchery",
        cascade="all, delete-orphan",
        order_by=SeawaterSourceSwitch.switched_at.desc(),
    )

    @property
    def latest_source_switch(self) -> Optional[SeawaterSourceSwitch]:
        return self.source_switches[0] if self.source_switches else None

    @property
    def source_confirmation_open(self) -> bool:
        """最近一次海水源切换是否仍在 24 小时确认窗内。"""
        latest = self.latest_source_switch
        if latest is None:
            return False
        switched_at = latest.switched_at
        if switched_at.tzinfo is None:
            switched_at = switched_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - switched_at < SOURCE_CONFIRMATION_WINDOW
