from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.source_switch_log import SourceSwitchLog
from app.models.user import User
from app.schemas.source_switch import SourceSwitchLogOut

router = APIRouter(prefix="/api/source-switches", tags=["source-switches"])


@router.get("", response_model=List[SourceSwitchLogOut])
def list_source_switches(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(SourceSwitchLog)
        .order_by(SourceSwitchLog.switched_at.desc(), SourceSwitchLog.id.desc())
        .all()
    )
