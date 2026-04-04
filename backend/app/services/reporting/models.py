from dataclasses import dataclass, field


@dataclass
class ReportSummary:
    name: str | None = None
    stats: dict | None = None
    status: str | None = None
    duration: int | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "stats": self.stats,
            "status": self.status,
            "duration": self.duration,
        }


@dataclass
class ReportEntry:
    id: str
    name: str
    created_at: str
    size: int
    entry_path: str | None = None
    stats: dict | None = None
    status: str | None = None
    duration: int | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "size": self.size,
            "entry_path": self.entry_path,
            "stats": self.stats,
            "status": self.status,
            "duration": self.duration,
        }


@dataclass
class HistoryFilterOptions:
    tags: list[str] = field(default_factory=list)
    suites: list[str] = field(default_factory=list)
    environments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tags": self.tags,
            "suites": self.suites,
            "environments": self.environments,
        }

    @classmethod
    def from_dict(cls, value: object) -> "HistoryFilterOptions":
        if not isinstance(value, dict):
            return cls()
        return cls(
            tags=[item for item in value.get("tags", []) if isinstance(item, str)],
            suites=[item for item in value.get("suites", []) if isinstance(item, str)],
            environments=[item for item in value.get("environments", []) if isinstance(item, str)],
        )


@dataclass
class HistoryRunRecord:
    uuid: str
    name: str | None
    timestamp: int

    def to_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, value: object) -> "HistoryRunRecord | None":
        if not isinstance(value, dict) or not isinstance(value.get("uuid"), str):
            return None
        name = value.get("name")
        timestamp = value.get("timestamp")
        return cls(
            uuid=value["uuid"],
            name=name if isinstance(name, str) else None,
            timestamp=int(timestamp) if isinstance(timestamp, int) else 0,
        )


@dataclass
class HistoryResultRecord:
    run_uuid: str | None
    run_name: str | None
    timestamp: int
    test_key: str
    name: str
    status: str | None
    duration: int | None
    start: int | None
    stop: int | None
    environment: str
    suite: str
    tags: list[str]
    signature: str
    message: str | None

    def to_dict(self) -> dict:
        return {
            "runUuid": self.run_uuid,
            "runName": self.run_name,
            "timestamp": self.timestamp,
            "testKey": self.test_key,
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "start": self.start,
            "stop": self.stop,
            "environment": self.environment,
            "suite": self.suite,
            "tags": self.tags,
            "signature": self.signature,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, value: object) -> "HistoryResultRecord | None":
        if not isinstance(value, dict):
            return None

        required_strings = {
            "test_key": value.get("testKey"),
            "name": value.get("name"),
            "environment": value.get("environment"),
            "suite": value.get("suite"),
            "signature": value.get("signature"),
        }
        if not all(isinstance(item, str) for item in required_strings.values()):
            return None

        return cls(
            run_uuid=value.get("runUuid") if isinstance(value.get("runUuid"), str) else None,
            run_name=value.get("runName") if isinstance(value.get("runName"), str) else None,
            timestamp=value.get("timestamp") if isinstance(value.get("timestamp"), int) else 0,
            test_key=required_strings["test_key"],
            name=required_strings["name"],
            status=value.get("status") if isinstance(value.get("status"), str) else None,
            duration=value.get("duration") if isinstance(value.get("duration"), int) else None,
            start=value.get("start") if isinstance(value.get("start"), int) else None,
            stop=value.get("stop") if isinstance(value.get("stop"), int) else None,
            environment=required_strings["environment"],
            suite=required_strings["suite"],
            tags=[item for item in value.get("tags", []) if isinstance(item, str)],
            signature=required_strings["signature"],
            message=value.get("message") if isinstance(value.get("message"), str) else None,
        )


@dataclass
class HistorySourceRecord:
    name: str
    size: int
    mtime_ns: int
    is_active: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, value: object) -> "HistorySourceRecord | None":
        if not isinstance(value, dict):
            return None
        name = value.get("name")
        size = value.get("size")
        mtime_ns = value.get("mtime_ns")
        is_active = value.get("is_active")
        if not isinstance(name, str) or not isinstance(size, int) or not isinstance(mtime_ns, int):
            return None
        return cls(
            name=name,
            size=size,
            mtime_ns=mtime_ns,
            is_active=is_active if isinstance(is_active, bool) else False,
        )


@dataclass
class HistoryIndexData:
    version: int
    source_size: int
    source_mtime_ns: int
    records: int
    runs: list[HistoryRunRecord]
    results: list[HistoryResultRecord]
    filter_options: HistoryFilterOptions
    source_files: list[HistorySourceRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "source_size": self.source_size,
            "source_mtime_ns": self.source_mtime_ns,
            "records": self.records,
            "runs": [run.to_dict() for run in self.runs],
            "results": [result.to_dict() for result in self.results],
            "filter_options": self.filter_options.to_dict(),
            "source_files": [source.to_dict() for source in self.source_files],
        }

    @classmethod
    def empty(cls, source_size: int = 0, source_mtime_ns: int = 0) -> "HistoryIndexData":
        return cls(
            version=2,
            source_size=source_size,
            source_mtime_ns=source_mtime_ns,
            records=0,
            runs=[],
            results=[],
            filter_options=HistoryFilterOptions(),
            source_files=[],
        )

    @classmethod
    def from_dict(cls, value: object) -> "HistoryIndexData":
        if not isinstance(value, dict):
            return cls.empty()

        runs: list[HistoryRunRecord] = []
        for item in value.get("runs", []):
            parsed = HistoryRunRecord.from_dict(item)
            if parsed is not None:
                runs.append(parsed)

        results: list[HistoryResultRecord] = []
        for item in value.get("results", []):
            parsed = HistoryResultRecord.from_dict(item)
            if parsed is not None:
                results.append(parsed)

        source_files: list[HistorySourceRecord] = []
        for item in value.get("source_files", []):
            parsed = HistorySourceRecord.from_dict(item)
            if parsed is not None:
                source_files.append(parsed)

        return cls(
            version=value.get("version") if isinstance(value.get("version"), int) else 1,
            source_size=value.get("source_size") if isinstance(value.get("source_size"), int) else 0,
            source_mtime_ns=(
                value.get("source_mtime_ns") if isinstance(value.get("source_mtime_ns"), int) else 0
            ),
            records=value.get("records") if isinstance(value.get("records"), int) else 0,
            runs=runs,
            results=results,
            filter_options=HistoryFilterOptions.from_dict(value.get("filter_options")),
            source_files=source_files,
        )
