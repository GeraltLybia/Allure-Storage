import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .analytics import HistoryAnalyticsService
from .common import coerce_int
from .context import StorageContext
from .history_index import HistoryIndexService
from .repositories import HistoryRepository

logger = logging.getLogger(__name__)


class HistoryService:
    _upload_chunk_size = 1024 * 1024
    _max_line_size = 64 * 1024 * 1024

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
        self._upload_lock = threading.Lock()

    def get_history_path(self) -> Path:
        if not self.context.history_file.exists():
            raise HTTPException(status_code=404, detail="History file not found")
        return self.repository.get_history_path()

    async def upload_history(self, file: UploadFile) -> dict:
        try:
            temp_path = await self.stream_upload_to_temp(file)
        finally:
            await file.close()
        return self.finalize_upload(temp_path)

    async def stream_upload_to_temp(self, file: UploadFile) -> Path:
        if not file.filename or not file.filename.lower().endswith(".jsonl"):
            raise HTTPException(status_code=400, detail="Only JSONL files are supported")

        temp_path = self.repository.create_upload_temp_path()
        try:
            written = await self._copy_and_validate(file, temp_path)
        except ValueError as exc:
            self.repository.delete_temp_file(temp_path)
            raise HTTPException(status_code=400, detail="Invalid JSONL format") from exc
        except HTTPException:
            self.repository.delete_temp_file(temp_path)
            raise
        except Exception:
            self.repository.delete_temp_file(temp_path)
            logger.exception("History upload failed during streaming")
            raise HTTPException(status_code=500, detail="Upload failed") from None
        logger.info("History upload staged: temp=%s size=%s", temp_path.name, written)
        return temp_path

    async def _copy_and_validate(self, file: UploadFile, temp_path: Path) -> int:
        carry = b""
        total_written = 0
        with temp_path.open("wb") as output:
            while True:
                chunk = await file.read(self._upload_chunk_size)
                if not chunk:
                    break
                data = carry + chunk if carry else chunk
                cut = data.rfind(b"\n")
                if cut == -1:
                    if len(data) > self._max_line_size:
                        raise ValueError("JSONL line is too long")
                    carry = data
                    continue
                complete = data[: cut + 1]
                carry = data[cut + 1 :]
                self._validate_lines(complete)
                total_written += len(complete)
                if total_written > self.context.max_upload_size_bytes:
                    raise HTTPException(status_code=413, detail="Upload file is too large")
                output.write(complete)
            if carry:
                self._validate_lines(carry)
                total_written += len(carry)
                if total_written > self.context.max_upload_size_bytes:
                    raise HTTPException(status_code=413, detail="Upload file is too large")
                output.write(carry)
        return total_written

    @staticmethod
    def _validate_lines(data: bytes) -> None:
        for raw_line in data.decode("utf-8").split("\n"):
            line = raw_line.strip()
            if line:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("JSONL lines must be objects")

    def finalize_upload(self, temp_path: Path) -> dict:
        with self._upload_lock:
            try:
                rotation_required = self.repository.history_limit_reached()
                if rotation_required:
                    self.repository.archive_current_history()
                    self.repository.replace_history(temp_path)
                    self.index_service.rebuild_index()
                    logger.info("History rotated: active file archived, new upload activated")
                else:
                    self.index_service.refresh_index(temp_path)
                    self.repository.replace_history(temp_path)
                return {"message": "History file updated successfully"}
            except ValueError as exc:
                self.repository.delete_temp_file(temp_path)
                raise HTTPException(status_code=400, detail="Invalid JSONL format") from exc
            except HTTPException:
                self.repository.delete_temp_file(temp_path)
                raise
            except Exception:
                self.repository.delete_temp_file(temp_path)
                logger.exception("History upload failed during finalize")
                raise HTTPException(status_code=500, detail="Upload failed") from None

    def history_info(self) -> dict:
        if not self.repository.has_any_history():
            return {"records": 0, "updated_at": None, "size": 0}

        self.index_service.ensure_index()
        index = self.index_service.load_index()
        stat = self.repository.read_history_stat() if self.context.history_file.exists() else None
        return {
            "records": coerce_int(index.records),
            "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat() if stat else None,
            "size": stat.st_size if stat else 0,
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
        if not self.repository.has_any_history():
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
        if not self.repository.has_any_history():
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