from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceSwitchCreate(BaseModel):
    """海水源切换登记：新水源摘要去空白后至少 4 字。"""

    new_source_summary: str = Field(..., alias="newSourceSummary")
    operator_name: str = Field(..., min_length=1, max_length=64, alias="operatorName")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("new_source_summary")
    @classmethod
    def validate_new_summary(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 4:
            raise ValueError("新水源摘要去空白后至少 4 个字")
        return v


class SourceSwitchLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    hatchery_id: int = Field(serialization_alias="hatcheryId")
    switched_at: datetime = Field(serialization_alias="switchedAt")
    old_source_summary: Optional[str] = Field(
        serialization_alias="oldSourceSummary"
    )
    new_source_summary: str = Field(serialization_alias="newSourceSummary")
    operator_name: str = Field(serialization_alias="operatorName")


class OpenConfirmCountOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    open_count: int = Field(serialization_alias="openCount")
