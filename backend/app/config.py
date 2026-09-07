import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Absolute default so the storage location does not depend on the process CWD.
DEFAULT_STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"


def _parse_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}") from exc
    if value < 1:
        raise ValueError(f"Environment variable {name} must be a positive integer, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    storage_root: Path
    reports_folder: Path
    history_file: Path
    history_archive_folder: Path
    history_index_file: Path
    max_reports: int
    max_history_file_size_bytes: int
    max_upload_size_bytes: int
    max_indexed_runs: int
    cors_origins: list[str] = field(default_factory=list)
    api_title: str = "TestReport Storage API"


def get_settings() -> Settings:
    storage_root = Path(os.getenv("APP_STORAGE_ROOT", str(DEFAULT_STORAGE_ROOT)))
    if not storage_root.is_absolute():
        storage_root = storage_root.resolve()
    reports_folder = storage_root / "reports"
    history_file = storage_root / "history.jsonl"
    history_archive_folder = storage_root / "history_archive"
    history_index_file = storage_root / "history_index.json"

    max_reports = _parse_positive_int("APP_MAX_REPORTS", 10)
    max_history_size_mb = _parse_positive_int("APP_HISTORY_MAX_FILE_SIZE_MB", 100)
    max_upload_size_mb = _parse_positive_int("APP_MAX_UPLOAD_SIZE_MB", 512)
    max_indexed_runs = _parse_positive_int("APP_MAX_INDEXED_RUNS", 1000)
    cors_origins = [
        item.strip()
        for item in os.getenv("APP_CORS_ORIGINS", "").split(",")
        if item.strip()
    ]

    settings = Settings(
        storage_root=storage_root,
        reports_folder=reports_folder,
        history_file=history_file,
        history_archive_folder=history_archive_folder,
        history_index_file=history_index_file,
        max_reports=max_reports,
        max_history_file_size_bytes=max_history_size_mb * 1024 * 1024,
        max_upload_size_bytes=max_upload_size_mb * 1024 * 1024,
        max_indexed_runs=max_indexed_runs,
        cors_origins=cors_origins,
    )
    logger.info(
        "Resolved settings: storage_root=%s max_reports=%s max_history_file_size_mb=%s "
        "max_upload_size_mb=%s max_indexed_runs=%s cors_origins=%s",
        settings.storage_root,
        settings.max_reports,
        max_history_size_mb,
        max_upload_size_mb,
        settings.max_indexed_runs,
        settings.cors_origins or "same-origin",
    )
    return settings