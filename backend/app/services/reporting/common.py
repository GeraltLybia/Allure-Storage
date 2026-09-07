import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

try:
    from fastapi import HTTPException
except ModuleNotFoundError:
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)


# Uncompressed size may grow at most 10x the archive size (plus a 64 MiB floor).
ZIP_SIZE_MULTIPLIER = 10
ZIP_MIN_SIZE_LIMIT = 64 * 1024 * 1024
ZIP_CHUNK_SIZE = 1024 * 1024

# File type bits (upper 12 bits of external_attr) that must never be extracted.
_UNSAFE_FILE_MODES = {
    0o120000,  # symlink
    0o060000,  # character device
    0o020000,  # block device
    0o010000,  # fifo
}


def coerce_int(value: object) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def coerce_optional_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def normalize_status(value: object) -> str:
    return value.strip().lower() if isinstance(value, str) and value.strip() else "unknown"


def percentile(values: list[int], q: int) -> int | None:
    if not values:
        return None
    index = min(len(values) - 1, round((q / 100) * (len(values) - 1)))
    return values[index]


def is_date_like_dir(value: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}([_-].+)?$", value))


def cleanup_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _member_file_mode(member: zipfile.ZipInfo) -> int:
    return (member.external_attr >> 28) & 0o170000


def _is_unsafe_member(member: zipfile.ZipInfo) -> bool:
    return _member_file_mode(member) in _UNSAFE_FILE_MODES


def _resolve_member_path(destination: Path, destination_resolved: Path, member: zipfile.ZipInfo) -> Path:
    if member.filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Archive contains invalid paths")
    if ".." in Path(member.filename).parts:
        raise HTTPException(status_code=400, detail="Archive contains invalid paths")
    resolved = (destination / member.filename).resolve()
    if resolved != destination_resolved and destination_resolved not in resolved.parents:
        raise HTTPException(status_code=400, detail="Archive contains invalid paths")
    return resolved


def safe_extract_zip(
    archive: zipfile.ZipFile,
    destination: Path,
    max_uncompressed_size: int | None = None,
) -> None:
    """Extract a ZIP archive with per-member validation, right before extraction.

    Rejects symlinks/devices/FIFOs, absolute paths and ``..`` traversal, and
    aborts when the cumulative uncompressed size exceeds the limit (zip bomb
    protection).
    """
    destination_resolved = destination.resolve()

    if max_uncompressed_size is None:
        archive_size = 0
        archive_filename = archive.filename
        if archive_filename:
            try:
                archive_size = os.path.getsize(archive_filename)
            except OSError:
                archive_size = 0
        max_uncompressed_size = max(ZIP_MIN_SIZE_LIMIT, archive_size * ZIP_SIZE_MULTIPLIER)

    total_uncompressed = 0
    for member in archive.infolist():
        if _is_unsafe_member(member):
            raise HTTPException(status_code=400, detail="Archive contains invalid paths")
        member_path = _resolve_member_path(destination, destination_resolved, member)

        if member.is_dir():
            member_path.mkdir(parents=True, exist_ok=True)
            continue

        member_path.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, member_path.open("wb") as target:
            while True:
                chunk = source.read(ZIP_CHUNK_SIZE)
                if not chunk:
                    break
                total_uncompressed += len(chunk)
                if total_uncompressed > max_uncompressed_size:
                    raise HTTPException(
                        status_code=400,
                        detail="Archive uncompressed size exceeds the allowed limit",
                    )
                target.write(chunk)


def validate_jsonl(content: bytes) -> None:
    for raw_line in content.decode("utf-8").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("JSONL lines must be objects")


def files_share_prefix(left: Path, right: Path, size: int) -> bool:
    if size <= 0:
        return True
    chunk_size = 1024 * 1024
    with left.open("rb") as left_file, right.open("rb") as right_file:
        remaining = size
        while remaining > 0:
            current_chunk = min(chunk_size, remaining)
            if left_file.read(current_chunk) != right_file.read(current_chunk):
                return False
            remaining -= current_chunk
    return True


def build_run_label(name: object, timestamp: object, fallback: str) -> str:
    if isinstance(name, str) and name.strip():
        return name
    try:
        date = datetime.fromtimestamp(coerce_int(timestamp) / 1000)
        return date.isoformat(sep=" ", timespec="minutes")
    except Exception:
        return fallback