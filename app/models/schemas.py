"""Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MeasurementResponse(BaseModel):
    feature_index: int
    geometry_type: str
    measurement_type: Optional[str] = None
    measurement_value: Optional[float] = None
    unit: Optional[str] = None


class FileInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    feature_count: int
    crs: Optional[str] = None
    status: str


class MeasurementsResponse(BaseModel):
    file_id: str
    total_features: int
    measurements: List[MeasurementResponse]


class SummaryResponse(BaseModel):
    file_id: str
    total_features: int
    polygon_count: int
    linestring_count: int
    point_count: int
    total_area_m2: float
    total_length_m: float