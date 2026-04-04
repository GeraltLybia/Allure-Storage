from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    storage_root: Path
    reports_folder: Path
    history_file: Path
    history_archive_folder: Path
    history_index_file: Path
    max_reports: int
    max_history_file_size_bytes: int
    api_title: str = "TestReport Storage API"



def get_settings() -> Settings:
    storage_root = Path(os.getenv("APP_STORAGE_ROOT", "storage"))
    reports_folder = storage_root / "reports"
    history_file = storage_root / "history.jsonl"
    history_archive_folder = storage_root / "history_archive"
    history_index_file = storage_root / "history_index.json"
    raw_max_reports = os.getenv("APP_MAX_REPORTS", "10")
    raw_max_history_size_mb = os.getenv("APP_HISTORY_MAX_FILE_SIZE_MB", "100")
    try:
        max_reports = max(1, int(raw_max_reports))
    except ValueError:
        max_reports = 10
    try:
        max_history_size_mb = max(1, int(raw_max_history_size_mb))
    except ValueError:
        max_history_size_mb = 100

    return Settings(
        storage_root=storage_root,
        reports_folder=reports_folder,
        history_file=history_file,
        history_archive_folder=history_archive_folder,
        history_index_file=history_index_file,
        max_reports=max_reports,
        max_history_file_size_bytes=max_history_size_mb * 1024 * 1024,
    )
