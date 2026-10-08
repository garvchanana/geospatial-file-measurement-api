
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    id: str = Field(..., examples=["abc123"])
    filename: str = Field(..., examples=["survey.kml"])
    stored_filename: str = Field(..., examples=["abc123.kml"])
    content_type: str | None = Field(default=None, examples=["application/vnd.google-earth.kml+xml"])
    file_size_bytes: int = Field(..., examples=[2048])
    feature_count: int | None = Field(default=None, examples=[120])
    crs: str | None = Field(default=None, examples=["EPSG:4326"])
    status: str = Field(..., examples=["COMPLETED"])
    uploaded_at: datetime
    message: str = Field(..., examples=["File uploaded successfully."])


class FileInfoResponse(BaseModel):
    id: str = Field(..., examples=["abc123"])
    filename: str = Field(..., examples=["survey.kml"])
    stored_filename: str = Field(..., examples=["abc123.kml"])
    feature_count: int = Field(..., examples=[120])
    crs: str | None = Field(default=None, examples=["EPSG:4326"])
    status: str = Field(..., examples=["COMPLETED"])
    uploaded_at: datetime


class FeatureInfo(BaseModel):
    index: int = Field(..., examples=[0])
    geometry_type: str | None = Field(default=None, examples=["Polygon"])
    geometry: dict[str, Any] | None = None
    crs: str | None = Field(default=None, examples=["EPSG:4326"])
    properties: dict[str, Any] = Field(default_factory=dict)


class GeospatialReadResult(BaseModel):
    filename: str = Field(..., examples=["survey.kml"])
    feature_count: int = Field(..., examples=[120])
    crs: str | None = Field(default=None, examples=["EPSG:4326"])
    features: list[FeatureInfo]


class FeatureMeasurement(BaseModel):
    feature_index: int = Field(..., examples=[0])
    geometry_type: str | None = Field(default=None, examples=["Polygon"])
    measurement_type: str | None = Field(default=None, examples=["area"])
    value: float | None = Field(default=None, examples=[12345.67])
    unit: str | None = Field(default=None, examples=["square_meters"])
    source_crs: str | None = Field(default=None, examples=["EPSG:4326"])
    measurement_crs: str | None = Field(default=None, examples=["EPSG:32643"])
    message: str


class FileMeasurementsResponse(BaseModel):
    id: str = Field(..., examples=["abc123"])
    filename: str = Field(..., examples=["survey.kml"])
    feature_count: int = Field(..., examples=[120])
    source_crs: str | None = Field(default=None, examples=["EPSG:4326"])
    measurements: list[FeatureMeasurement]


class FileFeaturesResponse(BaseModel):
    id: str = Field(..., examples=["abc123"])
    filename: str = Field(..., examples=["survey.kml"])
    feature_count: int = Field(..., examples=[120])
    crs: str | None = Field(default=None, examples=["EPSG:4326"])
    features: list[FeatureInfo]


class ProcessedFileRecord(BaseModel):
    id: str
    filename: str
    stored_filename: str
    content_type: str | None = None
    file_size_bytes: int
    feature_count: int
    crs: str | None = None
    status: str
    uploaded_at: datetime
    features: list[FeatureInfo]
