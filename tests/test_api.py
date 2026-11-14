from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.config import PROJECT_ROOT, Settings
from backend.app.db.database import Database
from backend.app.main import create_app
from backend.app.services.project_service import ProjectNotFoundError, ProjectService


def build_service(tmp_path: Path) -> tuple[Settings, ProjectService]:
    settings = Settings(
        app_name="test",
        database_path=tmp_path / "test.db",
        frontend_dir=PROJECT_ROOT / "frontend",
        pointcloud_dir=(
            PROJECT_ROOT
            / "Task-of-2026-05-09T002602746Z-all"
            / "entwine_pointcloud"
        ),
        public_project_slug="webodm-demo",
        log_level="WARNING",
    )

    database = Database(settings.database_path)
    database.initialize()
    service = ProjectService(
        database=database,
        pointcloud_dir=settings.pointcloud_dir,
        project_slug=settings.public_project_slug,
    )
    service.seed_public_project()
    return settings, service


def test_public_project_and_dataset_metadata(tmp_path: Path) -> None:
    settings, service = build_service(tmp_path)

    projects = service.list_published()
    assert len(projects) == 1
    assert projects[0].slug == "webodm-demo"
    assert projects[0].title == "空拍數位地景"

    dataset = service.get_primary_dataset("webodm-demo")
    assert dataset.point_count == 5_150_570
    assert dataset.epsg == 32651
    assert dataset.ept_path == "ept.json"
    assert len(dataset.bounds) == 6
    assert dataset.size_bytes > 0

    ept = json.loads((settings.pointcloud_dir / dataset.ept_path).read_text("utf-8"))
    assert ept["points"] == dataset.point_count


def test_unknown_project_and_route_contract(tmp_path: Path) -> None:
    settings, service = build_service(tmp_path)
    with pytest.raises(ProjectNotFoundError):
        service.get_published("not-found")

    app = create_app(settings)
    paths = {route.path for route in app.routes}
    assert "/api/v1/health" in paths
    assert "/api/v1/projects/{slug}" in paths
    assert "/api/v1/projects/{slug}/point-cloud" in paths
    assert "/api/v1/projects/{slug}/annotations" in paths
