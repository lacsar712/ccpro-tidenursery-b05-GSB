from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HatcheryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    seawater_source: str = Field(..., min_length=1, max_length=128, alias="seawaterSource")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class HatcheryUpdate(BaseModel):
    # 海水源字段不允许在此直接修改：水源变更必须走切换日志接口。
    # extra="forbid"：普通 PUT 请求携带 seawaterSource 时直接 400 拒绝，
    # 杜绝只改场字段不写日志。
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class HatcheryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    seawater_source: str = Field(serialization_alias="seawaterSource")
    notes: Optional[str] = None
    source_confirmation_open: bool = Field(
        serialization_alias="sourceConfirmationOpen"
    )
