from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.hatchery import Hatchery
from app.models.source_switch_log import SourceSwitchLog
from app.models.user import User
from app.schemas.hatchery import HatcheryCreate, HatcheryUpdate, HatcheryOut
from app.schemas.source_switch import OpenConfirmCountOut, SourceSwitchCreate, SourceSwitchLogOut
from app.source_window import open_hatchery_ids

router = APIRouter(prefix="/api/hatcheries", tags=["hatcheries"])


def _to_out(item: Hatchery, open_ids: set[int]) -> HatcheryOut:
    return HatcheryOut.model_validate(
        {
            "id": item.id,
            "name": item.name,
            "seawater_source": item.seawater_source,
            "notes": item.notes,
            "source_confirmation_open": item.id in open_ids,
        }
    )


@router.get("", response_model=List[HatcheryOut])
def list_hatcheries(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.query(Hatchery).order_by(Hatchery.id).all()
    open_ids = open_hatchery_ids(db)
    return [_to_out(item, open_ids) for item in items]


@router.post("", response_model=HatcheryOut, status_code=status.HTTP_201_CREATED)
def create_hatchery(
    payload: HatcheryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = Hatchery(
        name=payload.name,
        seawater_source=payload.seawater_source,
        notes=payload.notes,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="育苗场名称已存在")
    db.refresh(item)
    return _to_out(item, open_hatchery_ids(db))


@router.get("/source-confirmations/open-count", response_model=OpenConfirmCountOut)
def open_confirmation_count(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return OpenConfirmCountOut(open_count=len(open_hatchery_ids(db)))


@router.get("/{hatchery_id}", response_model=HatcheryOut)
def get_hatchery(
    hatchery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="育苗场不存在")
    return _to_out(item, open_hatchery_ids(db))


@router.put("/{hatchery_id}", response_model=HatcheryOut)
def update_hatchery(
    hatchery_id: int,
    payload: HatcheryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="育苗场不存在")
    data = payload.model_dump(exclude_unset=True)
    # 海水源字段不在 HatcheryUpdate 中：禁止只改场字段而不写切换日志
    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="育苗场名称已存在")
    db.refresh(item)
    return _to_out(item, open_hatchery_ids(db))


@router.get("/{hatchery_id}/source-switches", response_model=List[SourceSwitchLogOut])
def list_source_switches(
    hatchery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="育苗场不存在")
    return (
        db.query(SourceSwitchLog)
        .filter(SourceSwitchLog.hatchery_id == hatchery_id)
        .order_by(SourceSwitchLog.switched_at.desc(), SourceSwitchLog.id.desc())
        .all()
    )


@router.post(
    "/{hatchery_id}/source-switches",
    response_model=SourceSwitchLogOut,
    status_code=status.HTTP_201_CREATED,
)
def register_source_switch(
    hatchery_id: int,
    payload: SourceSwitchCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="育苗场不存在")

    new_summary = payload.new_source_summary.strip()
    # 写切换日志与更新育苗场海水源字段必须在同一事务内完成，
    # 禁止只写日志不改场字段，也禁止只改场字段不写日志。
    log = SourceSwitchLog(
        hatchery_id=item.id,
        switched_at=datetime.now(timezone.utc),
        old_source_summary=item.seawater_source,
        new_source_summary=new_summary,
        operator_name=payload.operator_name,
    )
    db.add(log)
    item.seawater_source = new_summary
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="海水源切换登记失败")
    db.refresh(log)
    return log


@router.delete("/{hatchery_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hatchery(
    hatchery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="育苗场不存在")
    db.delete(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该育苗场下仍有塘口，无法删除")
