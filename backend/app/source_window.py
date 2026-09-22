"""海水源切换确认窗口的共享判定逻辑。

切换时刻起 24 小时内，该场下属塘口新建/更新水质样必须携带与新水源摘要
（去空白后）一致的水源确认，否则 409。
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.hatchery import Hatchery
from app.models.source_switch_log import SOURCE_CONFIRM_WINDOW_HOURS, SourceSwitchLog


def window_lower_bound(now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now - timedelta(hours=SOURCE_CONFIRM_WINDOW_HOURS)


def latest_switch(
    db: Session, hatchery_id: int, now: Optional[datetime] = None
) -> Optional[SourceSwitchLog]:
    """该场最近一次切换日志（可能已超出确认窗）。"""
    return (
        db.query(SourceSwitchLog)
        .filter(SourceSwitchLog.hatchery_id == hatchery_id)
        .order_by(SourceSwitchLog.switched_at.desc(), SourceSwitchLog.id.desc())
        .first()
    )


def open_switch(
    db: Session, hatchery_id: int, now: Optional[datetime] = None
) -> Optional[SourceSwitchLog]:
    """若该场当前处于水源确认窗内，返回对应的最近一次切换日志，否则 None。"""
    latest = latest_switch(db, hatchery_id, now=now)
    if latest is None:
        return None
    switched_at = latest.switched_at
    if switched_at.tzinfo is None:
        switched_at = switched_at.replace(tzinfo=timezone.utc)
    if switched_at >= window_lower_bound(now):
        return latest
    return None


def open_hatchery_ids(db: Session, now: Optional[datetime] = None) -> set[int]:
    """所有当前处于确认窗内的育苗场 ID（与开放确认窗场数接口口径一致）。"""
    now = now or datetime.now(timezone.utc)
    lower = window_lower_bound(now)
    # 每个场最近一次切换时刻仍在窗口内
    rows = (
        db.query(SourceSwitchLog.hatchery_id)
        .group_by(SourceSwitchLog.hatchery_id)
        .having(func.max(SourceSwitchLog.switched_at) >= lower)
        .all()
    )
    return {hatchery_id for hatchery_id, in rows}
