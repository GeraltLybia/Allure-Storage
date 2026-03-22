from functools import lru_cache

from .config import get_settings
from .services.storage_service import StorageService


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    settings = get_settings()
    return StorageService(
        reports_folder=settings.reports_folder,
        history_file=settings.history_file,
        history_index_file=settings.history_index_file,
        max_reports=settings.max_reports,
    )
