from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OutageType = Literal["power", "water", "internet", "mobile_data"]


class OutageCreate(BaseModel):
    outage_type: OutageType
    area: str = Field(min_length=2, max_length=120, examples=["Universitas, Bloemfontein"])
    description: str = Field(default="", max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class OutageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    outage_type: OutageType
    area: str
    description: str
    latitude: float | None
    longitude: float | None
    confirmations: int
    resolved: bool
    created_at: datetime
    resolved_at: datetime | None


class AreaSummary(BaseModel):
    area: str
    active_reports: int
    total_confirmations: int
