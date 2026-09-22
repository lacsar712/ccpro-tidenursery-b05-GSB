from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HatcheryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    seawater_source: str = Field(..., min_length=1, max_length=128, alias="seawaterSource")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class HatcheryUpdate(BaseModel):
    # 海水源不允许经普通编辑修改：必须走海水源切换登记接口（写切换日志并同事务改字段）
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
        default=False, serialization_alias="sourceConfirmationOpen"
    )
