from __future__ import annotations

import os
import shutil
import stat
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO


class ArchiveValidationError(ValueError):
    """Raised when an uploaded archive is unsafe or exceeds configured limits."""


MAX_ARCHIVE_MEMBERS = int(os.getenv("MAX_ARCHIVE_MEMBERS", "30000"))
MAX_EXTRACTED_BYTES = int(os.getenv("MAX_EXTRACTED_BYTES", str(4 * 1024**3)))
MAX_COMPRESSION_RATIO = int(os.getenv("MAX_COMPRESSION_RATIO", "300"))
COPY_CHUNK_BYTES = 1024 * 1024


def _validated_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    if not members:
        raise ArchiveValidationError("ZIP 是空的")
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ArchiveValidationError(f"ZIP 檔案數超過限制 {MAX_ARCHIVE_MEMBERS:,}")

    total_size = 0
    total_compressed = 0
    for info in members:
        if "\\" in info.filename:
            raise ArchiveValidationError("ZIP 內含不安全的路徑分隔符號")
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ArchiveValidationError("ZIP 內含不安全的路徑")
        unix_mode = info.external_attr >> 16
        if stat.S_ISLNK(unix_mode):
            raise ArchiveValidationError("ZIP 不可包含符號連結")
        total_size += info.file_size
        total_compressed += info.compress_size

    if total_size > MAX_EXTRACTED_BYTES:
        raise ArchiveValidationError(
            f"解壓縮容量超過限制 {MAX_EXTRACTED_BYTES / 1024**3:.1f} GB"
        )
    if total_compressed and total_size / total_compressed > MAX_COMPRESSION_RATIO:
        raise ArchiveValidationError("ZIP 壓縮比例異常，已停止解壓縮")
    return members


def extract_archive(uploaded_file: BinaryIO, destination: Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(uploaded_file) as archive:
            members = _validated_members(archive)
            for info in members:
                relative = PurePosixPath(info.filename)
                target = destination.joinpath(*relative.parts).resolve()
                if os.path.commonpath((destination, target)) != str(destination):
                    raise ArchiveValidationError("ZIP 嘗試寫入暫存目錄之外")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, COPY_CHUNK_BYTES)
    except (zipfile.BadZipFile, OSError) as error:
        shutil.rmtree(destination, ignore_errors=True)
        raise ArchiveValidationError(f"ZIP 無法解壓縮：{error}") from error


def remove_directory(path: Path, allowed_root: Path) -> None:
    resolved = path.resolve()
    root = allowed_root.resolve()
    if resolved == root or os.path.commonpath((root, resolved)) != str(root):
        raise ValueError("拒絕移除工作階段目錄之外的路徑")
    shutil.rmtree(resolved, ignore_errors=True)


def cleanup_expired_sessions(sessions_root: Path, max_age_seconds: int = 14_400) -> None:
    sessions_root.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - max_age_seconds
    for entry in sessions_root.iterdir():
        try:
            if entry.is_dir() and entry.stat().st_mtime < cutoff:
                remove_directory(entry, sessions_root)
        except OSError:
            continue
