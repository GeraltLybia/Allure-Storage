from functools import lru_cache

from .config import get_settings
from .services.reporting import (
    HistoryAnalyticsService,
    HistoryIndexService,
    HistoryService,
    ReportStorageService,
    StorageContext,
)
from .services.storage_service import StorageService


@lru_cache(maxsize=1)
def get_storage_context() -> StorageContext:
    settings = get_settings()
    return StorageContext(
        reports_folder=settings.reports_folder,
        history_file=settings.history_file,
        history_archive_folder=settings.history_archive_folder,
        history_index_file=settings.history_index_file,
        max_reports=settings.max_reports,
        max_history_file_size_bytes=settings.max_history_file_size_bytes,
    )


@lru_cache(maxsize=1)
def get_report_storage_service() -> ReportStorageService:
    return ReportStorageService(get_storage_context())


@lru_cache(maxsize=1)
def get_history_index_service() -> HistoryIndexService:
    return HistoryIndexService(get_storage_context())


@lru_cache(maxsize=1)
def get_history_service() -> HistoryService:
    index_service = get_history_index_service()
    analytics_service = HistoryAnalyticsService(index_service)
    return HistoryService(
        context=get_storage_context(),
        index_service=index_service,
        analytics_service=analytics_service,
    )


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    context = get_storage_context()
    return StorageService(
        reports_folder=context.reports_folder,
        history_file=context.history_file,
        history_index_file=context.history_index_file,
        max_reports=context.max_reports,
    )
