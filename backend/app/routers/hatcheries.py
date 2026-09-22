from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.hatchery import Hatchery, SOURCE_CONFIRMATION_WINDOW
from app.models.seawater_source_switch import SeawaterSourceSwitch
from app.models.user import User
from app.schemas.hatchery import HatcheryCreate, HatcheryUpdate, HatcheryOut
from app.schemas.seawater_source_switch import SourceSwitchCreate, SourceSwitchOut

router = APIRouter(prefix="/api/hatcheries", tags=["hatcheries"])


def count_open_confirmation_windows(db: Session) -> int:
    """处于 24 小时水源确认窗内的育苗场数。

    窗内若存在切换记录，该场最近一次切换必然也在窗内，
    因此对窗内记录按场去重即可，与列表行 sourceConfirmationOpen 口径一致。
    """
    since = datetime.now(timezone.utc) - SOURCE_CONFIRMATION_WINDOW
    return (
        db.query(func.count(func.distinct(SeawaterSourceSwitch.hatchery_id)))
        .filter(SeawaterSourceSwitch.switched_at >= since)
        .scalar()
        or 0
    )


@router.get("/source-confirmation-open-count")
def get_open_confirmation_count(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return {"count": count_open_confirmation_windows(db)}


@router.get("", response_model=List[HatcheryOut])
def list_hatcheries(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Hatchery).order_by(Hatchery.id).all()


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
    return item


@router.post(
    "/{hatchery_id}/source-switches",
    response_model=SourceSwitchOut,
    status_code=status.HTTP_201_CREATED,
)
def register_source_switch(
    hatchery_id: int,
    payload: SourceSwitchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """登记海水源切换：写切换日志并在同一事务更新场上的海水源字段。"""
    hatchery = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not hatchery:
        raise HTTPException(status_code=404, detail="育苗场不存在")

    new_summary = payload.new_source_summary.strip()
    log = SeawaterSourceSwitch(
        hatchery_id=hatchery.id,
        switched_at=datetime.now(timezone.utc),
        old_source_summary=hatchery.seawater_source,
        new_source_summary=new_summary,
        operator_name=current_user.display_name,
    )
    db.add(log)
    hatchery.seawater_source = new_summary
    try:
        # 日志与场字段同一事务提交：禁止只写日志不改字段，也禁止只改字段不写日志。
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="切换登记失败")
    db.refresh(log)
    return log


@router.get("/{hatchery_id}/source-switches", response_model=List[SourceSwitchOut])
def list_source_switches(
    hatchery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    hatchery = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not hatchery:
        raise HTTPException(status_code=404, detail="育苗场不存在")
    return (
        db.query(SeawaterSourceSwitch)
        .filter(SeawaterSourceSwitch.hatchery_id == hatchery_id)
        .order_by(SeawaterSourceSwitch.switched_at.desc())
        .all()
    )


@router.get("/{hatchery_id}", response_model=HatcheryOut)
def get_hatchery(
    hatchery_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Hatchery).filter(Hatchery.id == hatchery_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="育苗场不存在")
    return item


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
    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="育苗场名称已存在")
    db.refresh(item)
    return item


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
