from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .analytics import HistoryAnalyticsService
from .common import coerce_int, validate_jsonl
from .context import StorageContext
from .history_index import HistoryIndexService
from .repositories import HistoryRepository


class HistoryService:
    def __init__(
        self,
        context: StorageContext,
        index_service: HistoryIndexService,
        analytics_service: HistoryAnalyticsService,
    ):
        self.context = context
        self.index_service = index_service
        self.analytics_service = analytics_service
        self.context.ensure_directories()
        self.repository = HistoryRepository(context)

    def get_history_path(self) -> Path:
        if not self.context.history_file.exists():
            raise HTTPException(status_code=404, detail="History file not found")
        return self.repository.get_history_path()

    async def upload_history(self, file: UploadFile) -> dict:
        if not file.filename or not (
            file.filename.endswith(".jsonl") or file.filename.endswith(".json")
        ):
            raise HTTPException(status_code=400, detail="Only JSONL files are supported")

        temp_path = self.repository.create_upload_temp_path()
        try:
            content = await file.read()
            validate_jsonl(content)
            self.repository.write_history_bytes(content, temp_path)
            self.index_service.refresh_index(temp_path)
            self.repository.replace_history(temp_path)
            return {"message": "History file updated successfully"}
        except ValueError as exc:
            self.repository.delete_temp_file(temp_path)
            raise HTTPException(status_code=400, detail="Invalid JSONL format") from exc
        except HTTPException:
            self.repository.delete_temp_file(temp_path)
            raise
        except Exception as exc:
            self.repository.delete_temp_file(temp_path)
            raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc
        finally:
            await file.close()

    def history_info(self) -> dict:
        if not self.context.history_file.exists():
            return {"records": 0, "updated_at": None, "size": 0}

        self.index_service.ensure_index()
        index = self.index_service.load_index()
        stat = self.repository.read_history_stat()
        return {
            "records": coerce_int(index.records),
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size": stat.st_size,
        }

    def rebuild_history_index(self) -> dict:
        return self.index_service.rebuild_index()

    def get_history_dashboard(
        self,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
        stop_from: int | None = None,
        stop_to: int | None = None,
    ) -> dict:
        if not self.context.history_file.exists():
            return self.analytics_service.empty_dashboard()

        self.index_service.ensure_index()
        index = self.index_service.load_index()
        return self.analytics_service.get_dashboard(
            index=index,
            tags=tags,
            suite=suite,
            environment=environment,
            signature=signature,
            stop_from=stop_from,
            stop_to=stop_to,
        )

    def get_history_test_details(
        self,
        test_key: str,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
        stop_from: int | None = None,
        stop_to: int | None = None,
    ) -> dict | None:
        if not self.context.history_file.exists():
            return None

        self.index_service.ensure_index()
        index = self.index_service.load_index()
        return self.analytics_service.get_test_details(
            index=index,
            test_key=test_key,
            tags=tags,
            suite=suite,
            environment=environment,
            signature=signature,
            stop_from=stop_from,
            stop_to=stop_to,
        )
