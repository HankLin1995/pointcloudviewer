from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_path: Path
    frontend_dir: Path
    pointcloud_dir: Path
    public_project_slug: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name="空拍數位地景",
            database_path=Path(
                os.getenv(
                    "DATABASE_PATH",
                    PROJECT_ROOT / "runtime" / "digital_twin.db",
                )
            ).resolve(),
            frontend_dir=Path(
                os.getenv("FRONTEND_DIR", PROJECT_ROOT / "frontend")
            ).resolve(),
            pointcloud_dir=Path(
                os.getenv(
                    "POINTCLOUD_DIR",
                    PROJECT_ROOT
                    / "Task-of-2026-05-09T002602746Z-all"
                    / "entwine_pointcloud",
                )
            ).resolve(),
            public_project_slug=os.getenv("PUBLIC_PROJECT_SLUG", "webodm-demo"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
