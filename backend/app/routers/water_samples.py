from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.hatchery import Hatchery
from app.models.pond import Pond
from app.models.user import User
from app.models.water_sample import WaterSample
from app.schemas.water_sample import (
    WaterSampleCreate,
    WaterSampleOut,
    WaterSampleUpdate,
)

router = APIRouter(prefix="/api/water-samples", tags=["water-samples"])


def enforce_source_confirmation(
    db: Session, hatchery: Hatchery, confirmation: Optional[str]
) -> None:
    """确认窗内的新建/更新必须带水源确认，且与新水源摘要去空白后一致，否则 409。"""
    if not hatchery.source_confirmation_open:
        return
    latest = hatchery.latest_source_switch
    expected = (latest.new_source_summary or "").strip()
    provided = (confirmation or "").strip()
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该场海水源切换未满 24 小时，新建或更新水质样必须带水源确认",
        )
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"水源确认与新水源摘要不一致，应为：{expected}",
        )


@router.get("", response_model=List[WaterSampleOut])
def list_samples(
    pond_id: Optional[int] = Query(None, alias="pondId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(WaterSample)
    if pond_id is not None:
        q = q.filter(WaterSample.pond_id == pond_id)
    return q.order_by(WaterSample.sampled_at.desc()).all()


@router.post("", response_model=WaterSampleOut, status_code=status.HTTP_201_CREATED)
def create_sample(
    payload: WaterSampleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pond = db.query(Pond).filter(Pond.id == payload.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    enforce_source_confirmation(db, pond.hatchery, payload.source_confirmation)
    item = WaterSample(
        pond_id=payload.pond_id,
        sampled_at=payload.sampled_at,
        temp_c=payload.temp_c,
        salinity_ppt=payload.salinity_ppt,
        do_mg_l=payload.do_mg_l,
        ph=payload.ph,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{sample_id}", response_model=WaterSampleOut)
def update_sample(
    sample_id: int,
    payload: WaterSampleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(WaterSample).filter(WaterSample.id == sample_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="水质样不存在")

    data = payload.model_dump(exclude_unset=True)
    confirmation = data.pop("source_confirmation", None)

    target_pond_id = data["pond_id"] if "pond_id" in data else item.pond_id
    pond = db.query(Pond).filter(Pond.id == target_pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    # 改已有样缺确认同样拒绝（409）。
    enforce_source_confirmation(db, pond.hatchery, confirmation)

    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(WaterSample).filter(WaterSample.id == sample_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="水质样不存在")
    db.delete(item)
    db.commit()
