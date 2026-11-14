from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Project:
    id: int
    slug: str
    title: str
    subtitle: str
    description: str
    location_name: str
    processed_at: datetime | None


@dataclass(frozen=True)
class PointCloudDataset:
    id: int
    project_id: int
    name: str
    ept_path: str
    epsg: int
    point_count: int
    bounds: list[float]
    size_bytes: int


@dataclass(frozen=True)
class Annotation:
    id: int
    title: str
    description: str
    position: tuple[float, float, float]
