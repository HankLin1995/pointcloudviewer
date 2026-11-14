from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class EptValidationError(ValueError):
    """Raised when an extracted archive is not a valid EPT dataset."""


@dataclass(frozen=True)
class EptMetadata:
    root: Path
    ept_path: Path
    point_count: int
    epsg: str
    bounds: tuple[float, float, float, float, float, float]
    size_bytes: int


def _format_epsg(value: object) -> str:
    text = str(value or "未知").strip()
    if text.isdigit():
        return f"EPSG:{text}"
    if text.upper().startswith("EPSG:"):
        return text.upper()
    return text


def inspect_ept(extracted_root: Path) -> EptMetadata:
    candidates = [
        path
        for path in extracted_root.rglob("ept.json")
        if (path.parent / "ept-data").is_dir()
        and (path.parent / "ept-hierarchy").is_dir()
    ]
    if not candidates:
        raise EptValidationError(
            "ZIP 內找不到完整 EPT；需要 ept.json、ept-data 與 ept-hierarchy"
        )
    if len(candidates) > 1:
        raise EptValidationError("ZIP 內包含多組 EPT，請一次只上傳一個點雲")

    ept_path = candidates[0]
    try:
        payload = json.loads(ept_path.read_text(encoding="utf-8"))
        point_count = int(payload["points"])
        horizontal = payload.get("srs", {}).get("horizontal")
        raw_bounds = payload["boundsConforming"]
        bounds = tuple(float(value) for value in raw_bounds)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise EptValidationError(f"ept.json 格式不完整：{error}") from error

    if point_count < 1:
        raise EptValidationError("ept.json 的點數必須大於零")
    if len(bounds) != 6:
        raise EptValidationError("ept.json 的 boundsConforming 必須包含六個數值")

    dataset_root = ept_path.parent
    size_bytes = sum(
        path.stat().st_size for path in dataset_root.rglob("*") if path.is_file()
    )
    return EptMetadata(
        root=dataset_root,
        ept_path=ept_path,
        point_count=point_count,
        epsg=_format_epsg(horizontal),
        bounds=bounds,
        size_bytes=size_bytes,
    )
