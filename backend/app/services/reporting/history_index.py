import json
import uuid
from pathlib import Path

from fastapi import HTTPException

from .common import coerce_int, coerce_optional_int, files_share_prefix
from .context import StorageContext
from .models import (
    HistoryFilterOptions,
    HistoryIndexData,
    HistoryResultRecord,
    HistoryRunRecord,
    HistorySourceRecord,
)
from .repositories import HistoryRepository


class HistoryIndexService:
    def __init__(self, context: StorageContext):
        self.context = context
        self.context.ensure_directories()
        self.repository = HistoryRepository(context)

    def ensure_index(self) -> None:
        source_paths = self.repository.list_history_source_paths()
        if not source_paths:
            return

        if not self.repository.index_exists():
            self.write_index(self.build_history_index(source_paths))
            return

        try:
            index = self.load_index()
        except HTTPException:
            self.write_index(self.build_history_index(source_paths))
            return

        if index.version < 2:
            self.write_index(self.build_history_index(source_paths))
            return

        active_record = self.repository.get_source_record(self.repository.get_history_path(), is_active=True) if self.repository.history_exists() else None
        if self.archives_changed(index.source_files, self.repository.list_source_records()):
            self.write_index(self.build_history_index(source_paths))
            return

        indexed_active = self.get_active_source(index.source_files)
        if active_record is None and indexed_active is None:
            return

        if active_record is not None and indexed_active is not None:
            if (
                indexed_active.size == active_record.size
                and indexed_active.mtime_ns == active_record.mtime_ns
            ):
                return

            if active_record.size > indexed_active.size and indexed_active.size >= 0:
                index = self.append_index_from_offset(
                    index,
                    self.repository.get_history_path(),
                    indexed_active.size,
                    source_files=self.repository.list_source_records(),
                )
                self.write_index(index)
                return

        if active_record is None and indexed_active is not None:
            self.write_index(self.build_history_index(source_paths))
            return

        if active_record is not None and indexed_active is None:
            self.write_index(self.build_history_index(source_paths))
            return

        self.write_index(self.build_history_index(source_paths))

    def refresh_index(self, new_history_path: Path) -> None:
        source_paths = list(self.repository.list_history_archive_paths())
        source_paths.append(new_history_path)

        if not self.repository.index_exists():
            self.write_index(self.build_history_index(source_paths, active_path=new_history_path))
            return

        index = self.load_index()
        if index.version < 2:
            self.write_index(self.build_history_index(source_paths, active_path=new_history_path))
            return

        current_records = self.repository.list_source_records()
        temp_source_files = [
            record for record in current_records if not record.is_active
        ]
        temp_source_files.append(self.repository.get_source_record(new_history_path, is_active=True))

        if self.archives_changed(index.source_files, temp_source_files):
            self.write_index(self.build_history_index(source_paths, active_path=new_history_path))
            return

        indexed_active = self.get_active_source(index.source_files)
        if (
            indexed_active is not None
            and self.repository.history_exists()
            and new_history_path.stat().st_size >= indexed_active.size
            and files_share_prefix(
                self.repository.get_history_path(),
                new_history_path,
                indexed_active.size,
            )
        ):
            index = self.append_index_from_offset(
                index,
                new_history_path,
                indexed_active.size,
                source_files=temp_source_files,
            )
            self.write_index(index)
            return

        self.write_index(self.build_history_index(source_paths, active_path=new_history_path))

    def rebuild_index(self) -> dict:
        source_paths = self.repository.list_history_source_paths()
        if not source_paths:
            raise HTTPException(status_code=404, detail="History file not found")

        self.write_index(self.build_history_index(source_paths))
        return {"message": "History index rebuilt successfully"}

    def build_history_index(
        self,
        source_paths: list[Path],
        active_path: Path | None = None,
    ) -> HistoryIndexData:
        active_source_path = active_path or (
            self.repository.get_history_path() if self.repository.history_exists() else None
        )
        active_record = (
            self.repository.get_source_record(active_source_path, is_active=True)
            if active_source_path is not None and active_source_path.exists()
            else None
        )
        index = HistoryIndexData.empty(
            source_size=active_record.size if active_record else 0,
            source_mtime_ns=active_record.mtime_ns if active_record else 0,
        )
        for source_path in source_paths:
            index = self.append_index_from_offset(
                index,
                source_path,
                0,
                source_files=self.build_source_records(source_paths, active_source_path),
            )
        return index

    def append_index_from_offset(
        self,
        index: HistoryIndexData,
        source_path: Path,
        offset: int,
        source_files: list[HistorySourceRecord] | None = None,
    ) -> HistoryIndexData:
        run_ids = {run.uuid for run in index.runs}
        results = list(index.results)
        runs = list(index.runs)
        tags = set(index.filter_options.tags)
        suites = set(index.filter_options.suites)
        environments = set(index.filter_options.environments)
        records = index.records

        with self.repository.open_history_source(source_path) as source:
            if offset and source_path.suffix != ".gz":
                source.seek(offset)
            for raw_line in source:
                line = raw_line.strip()
                if not line:
                    continue

                run = json.loads(line)
                records += 1
                run_uuid = run.get("uuid")
                run_name = run.get("name") or run_uuid
                run_timestamp = coerce_int(run.get("timestamp"))

                if isinstance(run_uuid, str) and run_uuid not in run_ids:
                    runs.append(HistoryRunRecord(uuid=run_uuid, name=run_name, timestamp=run_timestamp))
                    run_ids.add(run_uuid)

                for result in (run.get("testResults") or {}).values():
                    compact = self.compact_history_result(result, run_uuid, run_name, run_timestamp)
                    results.append(compact)
                    tags.update(compact.tags)
                    if compact.suite:
                        suites.add(compact.suite)
                    environments.add(compact.environment)

        stat = source_path.stat()
        active_source = self.get_active_source(source_files or index.source_files)
        return HistoryIndexData(
            version=index.version,
            source_size=active_source.size if active_source else stat.st_size,
            source_mtime_ns=active_source.mtime_ns if active_source else stat.st_mtime_ns,
            records=records,
            runs=runs,
            results=results,
            filter_options=HistoryFilterOptions(
                tags=sorted(tags),
                suites=sorted(suites),
                environments=sorted(environments),
            ),
            source_files=list(source_files or index.source_files),
        )

    def load_index(self) -> HistoryIndexData:
        try:
            return self.repository.load_index()
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=500, detail=f"History index is invalid: {exc}") from exc

    def write_index(self, index: HistoryIndexData) -> None:
        self.repository.write_index(index)

    def compact_history_result(
        self,
        result: dict,
        run_uuid: str | None,
        run_name: str | None,
        run_timestamp: int,
    ) -> HistoryResultRecord:
        labels = result.get("labels") or []
        tags = sorted(
            {
                label.get("value")
                for label in labels
                if isinstance(label, dict)
                and label.get("name") == "tag"
                and isinstance(label.get("value"), str)
            }
        )
        suite = next(
            (
                label.get("value")
                for label in labels
                if isinstance(label, dict)
                and label.get("name") in {"suite", "parentSuite"}
                and isinstance(label.get("value"), str)
            ),
            "unknown",
        )
        environment = result.get("environment")
        environment_value = (
            environment.strip()
            if isinstance(environment, str) and environment.strip()
            else "unknown"
        )
        test_key = (
            result.get("fullName")
            or result.get("name")
            or result.get("historyId")
            or result.get("id")
            or str(uuid.uuid4())
        )
        return HistoryResultRecord(
            run_uuid=run_uuid,
            run_name=run_name,
            timestamp=run_timestamp,
            test_key=test_key,
            name=result.get("fullName") or result.get("name") or test_key,
            status=result.get("status") if isinstance(result.get("status"), str) else None,
            duration=coerce_optional_int(result.get("duration")),
            start=coerce_optional_int(result.get("start")),
            stop=coerce_optional_int(result.get("stop")),
            environment=environment_value,
            suite=suite if isinstance(suite, str) and suite else "unknown",
            tags=tags,
            signature=self.build_signature(result),
            message=self.extract_message(result),
        )

    @staticmethod
    def build_signature(result: dict) -> str:
        message = result.get("message")
        if isinstance(message, str) and message.strip():
            line = message.split("\n", 1)[0].strip()
            return f"{line[:90]}…" if len(line) > 90 else line
        trace = result.get("trace")
        if isinstance(trace, str) and trace.strip():
            line = trace.split("\n", 1)[0].strip()
            return f"{line[:90]}…" if len(line) > 90 else line
        return "Unknown failure"

    @staticmethod
    def extract_message(result: dict) -> str | None:
        message = result.get("message")
        if isinstance(message, str) and message.strip():
            return message.split("\n", 1)[0].strip()
        trace = result.get("trace")
        if isinstance(trace, str) and trace.strip():
            return trace.split("\n", 1)[0].strip()
        return None

    def empty_filter_options(self) -> dict:
        return HistoryFilterOptions().to_dict()

    def build_source_records(
        self,
        source_paths: list[Path],
        active_path: Path | None,
    ) -> list[HistorySourceRecord]:
        records: list[HistorySourceRecord] = []
        for source_path in source_paths:
            is_active = active_path is not None and source_path == active_path
            records.append(self.repository.get_source_record(source_path, is_active=is_active))
        return records

    @staticmethod
    def get_active_source(source_files: list[HistorySourceRecord]) -> HistorySourceRecord | None:
        return next((source for source in source_files if source.is_active), None)

    def archives_changed(
        self,
        indexed_sources: list[HistorySourceRecord],
        current_sources: list[HistorySourceRecord],
    ) -> bool:
        indexed_archives = sorted(
            (source.name, source.size, source.mtime_ns)
            for source in indexed_sources
            if not source.is_active
        )
        current_archives = sorted(
            (source.name, source.size, source.mtime_ns)
            for source in current_sources
            if not source.is_active
        )
        return indexed_archives != current_archives
