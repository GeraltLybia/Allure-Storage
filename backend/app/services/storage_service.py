from pathlib import Path
import os

from fastapi import UploadFile

from .reporting import (
    HistoryAnalyticsService,
    HistoryIndexService,
    HistoryService,
    ReportStorageService,
    StorageContext,
)


class StorageService:
    def __init__(
        self,
        reports_folder: Path,
        history_file: Path,
        history_index_file: Path,
        max_reports: int,
    ):
        raw_max_history_size_mb = os.getenv("APP_HISTORY_MAX_FILE_SIZE_MB", "100")
        try:
            max_history_size_bytes = max(1, int(raw_max_history_size_mb)) * 1024 * 1024
        except ValueError:
            max_history_size_bytes = 100 * 1024 * 1024
        self.context = StorageContext(
            reports_folder=reports_folder,
            history_file=history_file,
            history_archive_folder=history_file.parent / "history_archive",
            history_index_file=history_index_file,
            max_reports=max_reports,
            max_history_file_size_bytes=max_history_size_bytes,
        )
        self.context.ensure_directories()
        self.report_storage = ReportStorageService(self.context)
        self.history_index = HistoryIndexService(self.context)
        self.history_analytics = HistoryAnalyticsService(self.history_index)
        self.history_service = HistoryService(
            context=self.context,
            index_service=self.history_index,
            analytics_service=self.history_analytics,
        )

    def list_reports(self) -> list[dict]:
        return self.report_storage.list_reports()

    async def upload_report(self, file: UploadFile) -> dict:
        return await self.report_storage.upload_report(file)

    def get_history_path(self) -> Path:
        return self.history_service.get_history_path()

    async def upload_history(self, file: UploadFile) -> dict:
        return await self.history_service.upload_history(file)

    def history_info(self) -> dict:
        return self.history_service.history_info()

    def rebuild_history_index(self) -> dict:
        return self.history_service.rebuild_history_index()

    def get_history_dashboard(
        self,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
    ) -> dict:
        return self.history_service.get_history_dashboard(
            tags=tags,
            suite=suite,
            environment=environment,
            signature=signature,
        )

    def get_history_test_details(
        self,
        test_key: str,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
    ) -> dict | None:
        return self.history_service.get_history_test_details(
            test_key=test_key,
            tags=tags,
            suite=suite,
            environment=environment,
            signature=signature,
        )

    def delete_report(self, report_id: str) -> dict:
        return self.report_storage.delete_report(report_id)

    def create_report_archive(self, report_id: str) -> tuple[Path, str]:
        return self.report_storage.create_report_archive(report_id)
