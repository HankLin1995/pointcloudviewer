from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from frontend.services.archive_service import ArchiveValidationError, extract_archive
from frontend.services.ept_service import EptValidationError, inspect_ept


def build_ept_zip() -> io.BytesIO:
    buffer = io.BytesIO()
    payload = {
        "points": 1234,
        "srs": {"horizontal": 32651},
        "boundsConforming": [1, 2, 3, 11, 22, 33],
    }
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("entwine_pointcloud/ept.json", json.dumps(payload))
        archive.writestr("entwine_pointcloud/ept-data/0-0-0-0.laz", b"sample")
        archive.writestr("entwine_pointcloud/ept-hierarchy/0-0-0-0.json", "{}")
    buffer.seek(0)
    return buffer


def test_extract_and_inspect_ept(tmp_path: Path) -> None:
    destination = tmp_path / "extracted"
    extract_archive(build_ept_zip(), destination)

    metadata = inspect_ept(destination)

    assert metadata.point_count == 1234
    assert metadata.epsg == "EPSG:32651"
    assert metadata.bounds == (1.0, 2.0, 3.0, 11.0, 22.0, 33.0)
    assert metadata.size_bytes > 0


def test_rejects_path_traversal(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")
    buffer.seek(0)

    with pytest.raises(ArchiveValidationError, match="不安全"):
        extract_archive(buffer, tmp_path / "extracted")

    assert not (tmp_path / "outside.txt").exists()


def test_rejects_incomplete_ept(tmp_path: Path) -> None:
    (tmp_path / "ept.json").write_text("{}", encoding="utf-8")

    with pytest.raises(EptValidationError, match="找不到完整 EPT"):
        inspect_ept(tmp_path)
