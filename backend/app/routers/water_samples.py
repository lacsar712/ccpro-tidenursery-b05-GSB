from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.pond import Pond
from app.models.user import User
from app.models.water_sample import WaterSample
from app.schemas.water_sample import WaterSampleCreate, WaterSampleOut, WaterSampleUpdate
from app.source_window import open_switch

router = APIRouter(prefix="/api/water-samples", tags=["water-samples"])


def _enforce_source_confirmation(
    db: Session, pond: Pond, confirmation: Optional[str]
) -> None:
    """确认窗内新建/更新水质样必须携带与新水源摘要（去空白后）一致的确认，否则 409。"""
    switch = open_switch(db, pond.hatchery_id)
    if switch is None:
        return
    if confirmation is None or confirmation.strip() != switch.new_source_summary.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "该育苗场海水源刚切换，24 小时内新建或更新水质样必须携带与新水源摘要"
                f"（{switch.new_source_summary}）一致的水源确认"
            ),
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
    _enforce_source_confirmation(db, pond, payload.source_confirmation)
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
    pond = db.query(Pond).filter(Pond.id == item.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    _enforce_source_confirmation(db, pond, payload.source_confirmation)
    data = payload.model_dump(exclude_unset=True, exclude={"source_confirmation"})
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
