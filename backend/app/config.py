from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    storage_root: Path
    reports_folder: Path
    history_file: Path
    history_index_file: Path
    max_reports: int
    api_title: str = "Allure Reports Storage API"



def get_settings() -> Settings:
    storage_root = Path(os.getenv("APP_STORAGE_ROOT", "storage"))
    reports_folder = storage_root / "reports"
    history_file = storage_root / "history.jsonl"
    history_index_file = storage_root / "history_index.json"
    raw_max_reports = os.getenv("APP_MAX_REPORTS", "10")
    try:
        max_reports = max(1, int(raw_max_reports))
    except ValueError:
        max_reports = 10

    return Settings(
        storage_root=storage_root,
        reports_folder=reports_folder,
        history_file=history_file,
        history_index_file=history_index_file,
        max_reports=max_reports,
    )
