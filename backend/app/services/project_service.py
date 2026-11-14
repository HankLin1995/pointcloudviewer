from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from backend.app.db.database import Database
from backend.app.models.project import Annotation, PointCloudDataset, Project


logger = logging.getLogger(__name__)


class ProjectNotFoundError(LookupError):
    pass


class DatasetNotFoundError(LookupError):
    pass


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ProjectService:
    def __init__(
        self,
        database: Database,
        pointcloud_dir: Path,
        project_slug: str,
    ) -> None:
        self.database = database
        self.pointcloud_dir = pointcloud_dir
        self.project_slug = project_slug

    def seed_public_project(self) -> None:
        ept_path = self.pointcloud_dir / "ept.json"
        if not ept_path.is_file():
            raise FileNotFoundError(f"Missing EPT metadata: {ept_path}")

        ept = json.loads(ept_path.read_text(encoding="utf-8"))
        size_bytes = sum(
            item.stat().st_size
            for item in self.pointcloud_dir.rglob("*")
            if item.is_file()
        )

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    slug, title, subtitle, description, location_name,
                    processed_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'published')
                ON CONFLICT(slug) DO UPDATE SET
                    title = excluded.title,
                    subtitle = excluded.subtitle,
                    description = excluded.description,
                    location_name = excluded.location_name,
                    processed_at = excluded.processed_at,
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    self.project_slug,
                    "空拍數位地景",
                    "從空拍影像重建的三維地景",
                    "以 87 張空拍影像與地面控制點建立的 WebODM 三維成果。拖曳、縮放並切換顯示方式，從不同角度認識這片土地。",
                    "WebODM 示範測區",
                    "2026-05-09T01:30:42+00:00",
                ),
            )
            project_id = connection.execute(
                "SELECT id FROM projects WHERE slug = ?", (self.project_slug,)
            ).fetchone()["id"]
            connection.execute(
                "UPDATE point_cloud_datasets SET is_primary = 0 WHERE project_id = ?",
                (project_id,),
            )
            connection.execute(
                """
                INSERT INTO point_cloud_datasets (
                    project_id, name, ept_path, epsg, point_count,
                    bounds_json, size_bytes, is_primary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(project_id, ept_path) DO UPDATE SET
                    name = excluded.name,
                    epsg = excluded.epsg,
                    point_count = excluded.point_count,
                    bounds_json = excluded.bounds_json,
                    size_bytes = excluded.size_bytes,
                    is_primary = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    project_id,
                    "2026 WebODM 點雲",
                    "ept.json",
                    int(ept["srs"]["horizontal"]),
                    int(ept["points"]),
                    json.dumps(ept["boundsConforming"]),
                    size_bytes,
                ),
            )
        logger.info(
            "Public project seeded slug=%s points=%s size_bytes=%s",
            self.project_slug,
            ept["points"],
            size_bytes,
        )

    def list_published(self) -> list[Project]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, slug, title, subtitle, description, location_name, processed_at
                FROM projects
                WHERE status = 'published'
                ORDER BY processed_at DESC, id DESC
                """
            ).fetchall()
        return [self._project_from_row(row) for row in rows]

    def get_published(self, slug: str) -> Project:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, slug, title, subtitle, description, location_name, processed_at
                FROM projects
                WHERE slug = ? AND status = 'published'
                """,
                (slug,),
            ).fetchone()
        if row is None:
            raise ProjectNotFoundError(slug)
        return self._project_from_row(row)

    def get_primary_dataset(self, slug: str) -> PointCloudDataset:
        project = self.get_published(slug)
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT id, project_id, name, ept_path, epsg, point_count,
                       bounds_json, size_bytes
                FROM point_cloud_datasets
                WHERE project_id = ? AND is_primary = 1
                """,
                (project.id,),
            ).fetchone()
        if row is None:
            raise DatasetNotFoundError(slug)
        return PointCloudDataset(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            ept_path=row["ept_path"],
            epsg=row["epsg"],
            point_count=row["point_count"],
            bounds=json.loads(row["bounds_json"]),
            size_bytes=row["size_bytes"],
        )

    def list_annotations(self, slug: str) -> list[Annotation]:
        project = self.get_published(slug)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, description, position_x, position_y, position_z
                FROM annotations
                WHERE project_id = ? AND is_published = 1
                ORDER BY display_order, id
                """,
                (project.id,),
            ).fetchall()
        return [
            Annotation(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                position=(row["position_x"], row["position_y"], row["position_z"]),
            )
            for row in rows
        ]

    @staticmethod
    def _project_from_row(row: object) -> Project:
        return Project(
            id=row["id"],
            slug=row["slug"],
            title=row["title"],
            subtitle=row["subtitle"],
            description=row["description"],
            location_name=row["location_name"],
            processed_at=_parse_datetime(row["processed_at"]),
        )
