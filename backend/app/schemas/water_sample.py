from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_do(v: Optional[float]) -> Optional[float]:
    if v is None:
        return v
    if v <= 0:
        raise ValueError("溶解氧 doMgL 必须大于 0")
    return v


def _validate_ph(v: Optional[float]) -> Optional[float]:
    if v is None:
        return v
    if v < 6 or v > 9:
        raise ValueError("pH 必须在 6 到 9 之间")
    return v


class WaterSampleCreate(BaseModel):
    pond_id: int = Field(..., alias="pondId")
    sampled_at: datetime = Field(..., alias="sampledAt")
    temp_c: float = Field(..., alias="tempC")
    salinity_ppt: float = Field(..., alias="salinityPpt")
    do_mg_l: float = Field(..., alias="doMgL")
    ph: float
    notes: Optional[str] = None
    # 水源确认：切换后 24 小时确认窗内必填，且与新水源摘要去空白后一致
    source_confirmation: Optional[str] = Field(None, alias="sourceConfirmation")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("do_mg_l")
    @classmethod
    def validate_do(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("溶解氧 doMgL 必须大于 0")
        return v

    @field_validator("ph")
    @classmethod
    def validate_ph(cls, v: float) -> float:
        if v < 6 or v > 9:
            raise ValueError("pH 必须在 6 到 9 之间")
        return v


class WaterSampleUpdate(BaseModel):
    sampled_at: Optional[datetime] = Field(None, alias="sampledAt")
    temp_c: Optional[float] = Field(None, alias="tempC")
    salinity_ppt: Optional[float] = Field(None, alias="salinityPpt")
    do_mg_l: Optional[float] = Field(None, alias="doMgL")
    ph: Optional[float] = None
    notes: Optional[str] = None
    # 水源确认：确认窗内更新已有样同样必填，且与新水源摘要去空白后一致
    source_confirmation: Optional[str] = Field(None, alias="sourceConfirmation")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("do_mg_l")
    @classmethod
    def validate_do(cls, v: Optional[float]) -> Optional[float]:
        return _validate_do(v)

    @field_validator("ph")
    @classmethod
    def validate_ph(cls, v: Optional[float]) -> Optional[float]:
        return _validate_ph(v)


class WaterSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    sampled_at: datetime = Field(serialization_alias="sampledAt")
    temp_c: float = Field(serialization_alias="tempC")
    salinity_ppt: float = Field(serialization_alias="salinityPpt")
    do_mg_l: float = Field(serialization_alias="doMgL")
    ph: float
    notes: Optional[str] = None
