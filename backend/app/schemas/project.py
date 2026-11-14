from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    slug: str
    title: str
    subtitle: str
    location_name: str
    processed_at: datetime | None


class ProjectDetail(ProjectSummary):
    description: str


class ProjectList(BaseModel):
    items: list[ProjectSummary]


class PointCloudResponse(BaseModel):
    name: str
    ept_url: str
    epsg: int
    point_count: int = Field(ge=0)
    size_bytes: int = Field(ge=0)
    bounds: list[float] = Field(min_length=6, max_length=6)


class AnnotationResponse(BaseModel):
    id: int
    title: str
    description: str
    position: tuple[float, float, float]


class AnnotationList(BaseModel):
    items: list[AnnotationResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
    pointcloud: str
