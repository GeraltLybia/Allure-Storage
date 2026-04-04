import json
import gzip
import uuid
from datetime import datetime
from shutil import copyfileobj
from pathlib import Path

from ..context import StorageContext
from ..models import HistoryIndexData, HistorySourceRecord


class HistoryRepository:
    def __init__(self, context: StorageContext):
        self.context = context
        self.context.ensure_directories()

    def history_exists(self) -> bool:
        return self.context.history_file.exists()

    def index_exists(self) -> bool:
        return self.context.history_index_file.exists()

    def get_history_path(self) -> Path:
        return self.context.history_file

    def history_archive_exists(self) -> bool:
        return any(self.list_history_archive_paths())

    def has_any_history(self) -> bool:
        return self.history_exists() or self.history_archive_exists()

    def read_history_stat(self):
        return self.context.history_file.stat()

    def list_history_archive_paths(self) -> list[Path]:
        return sorted(
            [
                *self.context.history_archive_folder.glob("*.jsonl"),
                *self.context.history_archive_folder.glob("*.jsonl.gz"),
            ]
        )

    def list_history_source_paths(self) -> list[Path]:
        sources = list(self.list_history_archive_paths())
        if self.history_exists():
            sources.append(self.context.history_file)
        return sources

    def get_source_record(self, path: Path, is_active: bool = False) -> HistorySourceRecord:
        stat = path.stat()
        name = self.context.history_file.name if is_active else path.name
        return HistorySourceRecord(
            name=name,
            size=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
            is_active=is_active,
        )

    def list_source_records(self) -> list[HistorySourceRecord]:
        records = [
            self.get_source_record(path)
            for path in self.list_history_archive_paths()
        ]
        if self.history_exists():
            records.append(self.get_source_record(self.context.history_file, is_active=True))
        return records

    def create_upload_temp_path(self) -> Path:
        return self.context.history_file.with_suffix(".upload.tmp")

    def write_history_bytes(self, content: bytes, path: Path) -> None:
        path.write_bytes(content)

    def replace_history(self, source: Path) -> None:
        source.replace(self.context.history_file)

    def history_limit_reached(self) -> bool:
        return (
            self.history_exists()
            and self.context.history_file.stat().st_size >= self.context.max_history_file_size_bytes
        )

    def archive_current_history(self) -> Path | None:
        if not self.history_exists():
            return None
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        archive_path = self.context.history_archive_folder / (
            f"history-{timestamp}-{uuid.uuid4().hex[:8]}.jsonl.gz"
        )
        with self.context.history_file.open("rb") as source, gzip.open(archive_path, "wb") as target:
            copyfileobj(source, target)
        self.context.history_file.unlink()
        return archive_path

    def open_history_source(self, path: Path):
        if path.suffix == ".gz":
            return gzip.open(path, mode="rt", encoding="utf-8")
        return path.open("r", encoding="utf-8")

    def delete_temp_file(self, path: Path) -> None:
        path.unlink(missing_ok=True)

    def load_index(self) -> HistoryIndexData:
        payload = json.loads(self.context.history_index_file.read_text(encoding="utf-8"))
        return HistoryIndexData.from_dict(payload)

    def write_index(self, index: HistoryIndexData) -> None:
        temp_path = self.context.history_index_file.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(index.to_dict(), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temp_path.replace(self.context.history_index_file)
