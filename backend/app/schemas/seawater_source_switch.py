from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceSwitchCreate(BaseModel):
    """登记海水源切换；new_source_summary 去空白后至少 4 字。"""

    new_source_summary: str = Field(..., alias="newSourceSummary")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("new_source_summary")
    @classmethod
    def validate_new_source(cls, v: str) -> str:
        summary = v.strip()
        if len(summary) < 4:
            raise ValueError("新水源摘要去空白后至少 4 个字")
        if len(summary) > 128:
            raise ValueError("新水源摘要不能超过 128 个字")
        return summary


class SourceSwitchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    hatchery_id: int = Field(serialization_alias="hatcheryId")
    switched_at: datetime = Field(serialization_alias="switchedAt")
    old_source_summary: Optional[str] = Field(
        serialization_alias="oldSourceSummary"
    )
    new_source_summary: str = Field(serialization_alias="newSourceSummary")
    operator_name: str = Field(serialization_alias="operatorName")
