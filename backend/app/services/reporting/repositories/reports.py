import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..common import coerce_int, is_date_like_dir
from ..context import StorageContext
from ..models import ReportEntry, ReportSummary

REPORT_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
META_FILENAME = "report.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class ReportsRepository:
    def __init__(self, context: StorageContext):
        self.context = context
        self.context.ensure_directories()

    def list_report_entries(self) -> list[ReportEntry]:
        if not self.context.reports_folder.exists():
            return []

        entries: list[ReportEntry] = []
        for report_dir in self.context.reports_folder.iterdir():
            if not report_dir.is_dir() or report_dir.name.startswith("."):
                continue

            meta = self.read_report_meta(report_dir)
            if meta is None:
                meta = self.build_report_meta(report_dir)
                self.write_report_meta(report_dir, meta)

            entries.append(
                ReportEntry(
                    id=report_dir.name,
                    name=meta["name"] or report_dir.name,
                    created_at=meta["created_at"],
                    size=meta["size"],
                    entry_path=meta["entry_path"],
                    stats=meta["stats"],
                    status=meta["status"],
                    duration=meta["duration"],
                )
            )

        return sorted(entries, key=lambda item: item.created_at, reverse=True)

    def resolve_report_dir(self, report_id: str) -> Path | None:
        """Single guard for every id-based operation.

        Rejects anything that is not a canonical uuid4 id, lives outside the
        reports folder, or is not an existing directory.
        """
        if not isinstance(report_id, str) or not REPORT_ID_RE.match(report_id):
            return None
        report_dir = (self.context.reports_folder / report_id).resolve()
        if report_dir.parent != self.context.reports_folder.resolve():
            return None
        if not report_dir.is_dir():
            return None
        return report_dir

    def create_report_directory(self, report_id: str) -> Path:
        report_path = self.context.reports_folder / report_id
        report_path.mkdir(parents=True, exist_ok=True)
        return report_path

    def report_exists(self, report_id: str) -> bool:
        return self.resolve_report_dir(report_id) is not None

    def delete_report(self, report_id: str) -> None:
        report_dir = self.resolve_report_dir(report_id)
        if report_dir is None:
            return
        shutil.rmtree(report_dir)

    def create_archive(self, report_id: str) -> tuple[Path, str]:
        report_dir = self.resolve_report_dir(report_id)
        if report_dir is None:
            raise FileNotFoundError(report_id)
        # Unique per-request name so concurrent downloads of the same report
        # never build/serve/unlink each other's archive.
        zip_path = self.context.reports_folder / f".{report_id}-{uuid.uuid4().hex}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", report_dir)
        return zip_path, f"{report_id}.zip"

    def remove_path(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path)

    def apply_retention(self) -> list[str]:
        report_dirs = [path for path in self.context.reports_folder.iterdir() if path.is_dir()]
        if len(report_dirs) <= self.context.max_reports:
            return []

        report_dirs.sort(key=self._created_sort_key)
        evicted: list[str] = []
        for old_report_dir in report_dirs[: len(report_dirs) - self.context.max_reports]:
            shutil.rmtree(old_report_dir)
            evicted.append(old_report_dir.name)
        return evicted

    def _created_sort_key(self, report_dir: Path) -> datetime:
        meta = self.read_report_meta(report_dir)
        if meta is not None:
            parsed = _parse_iso(meta.get("created_at"))
            if parsed is not None:
                return parsed
        try:
            return datetime.fromtimestamp(report_dir.stat().st_mtime, tz=timezone.utc)
        except OSError:
            return datetime.now(timezone.utc)

    def build_report_meta(self, report_dir: Path) -> dict:
        report_root = self.resolve_report_root(report_dir)
        summary = self.read_report_summary(report_dir, report_root)
        size = sum(
            file_path.stat().st_size
            for file_path in report_dir.rglob("*")
            if file_path.is_file()
        )
        try:
            created_at = datetime.fromtimestamp(report_dir.stat().st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            created_at = _utc_now_iso()
        return {
            "created_at": created_at,
            "size": size,
            "name": summary.name,
            "entry_path": self.build_entry_path(report_dir, report_root),
            "stats": summary.stats,
            "status": summary.status,
            "duration": summary.duration,
        }

    def read_report_meta(self, report_dir: Path) -> dict | None:
        meta_path = report_dir / META_FILENAME
        if not meta_path.is_file():
            return None
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            return None
        if not isinstance(payload, dict) or not _parse_iso(payload.get("created_at")):
            return None
        return {
            "created_at": payload["created_at"],
            "size": coerce_int(payload.get("size")),
            "name": payload.get("name") if isinstance(payload.get("name"), str) else None,
            "entry_path": payload.get("entry_path") if isinstance(payload.get("entry_path"), str) else None,
            "stats": payload.get("stats") if isinstance(payload.get("stats"), dict) else None,
            "status": payload.get("status") if isinstance(payload.get("status"), str) else None,
            "duration": coerce_int(payload.get("duration")) or None,
        }

    def write_report_meta(self, report_dir: Path, meta: dict) -> None:
        meta_path = report_dir / META_FILENAME
        try:
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
        except OSError:
            # Metadata is an optimization; a failed write must not break uploads.
            pass

    def resolve_report_root(self, report_dir: Path) -> Path | None:
        index_in_root = report_dir / "index.html"
        if index_in_root.exists():
            return report_dir

        candidates: list[Path] = []
        for index_path in report_dir.rglob("index.html"):
            if "__MACOSX" not in index_path.parts:
                candidates.append(index_path.parent)

        if not candidates:
            return None

        candidates.sort(
            key=lambda path: (
                0 if is_date_like_dir(path.name) else 1,
                len(path.relative_to(report_dir).parts),
                path.as_posix(),
            )
        )
        return candidates[0]

    def build_entry_path(self, report_dir: Path, report_root: Path | None) -> str | None:
        if report_root is None:
            return None
        relative_root = report_root.relative_to(report_dir)
        if not relative_root.parts:
            return f"{report_dir.name}/index.html"
        return f"{report_dir.name}/{relative_root.as_posix()}/index.html"

    def read_report_summary(self, report_dir: Path, report_root: Path | None) -> ReportSummary:
        candidates: list[Path] = []
        if report_root is not None:
            candidates.append(report_root / "summary.json")
        candidates.append(report_dir / "summary.json")

        for summary_path in report_dir.rglob("summary.json"):
            if "__MACOSX" not in summary_path.parts and summary_path not in candidates:
                candidates.append(summary_path)

        for summary_path in candidates:
            if not summary_path.exists() or not summary_path.is_file():
                continue

            try:
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
                stats = payload.get("stats") or {}
                status = payload.get("status")
                return ReportSummary(
                    name=payload.get("name") if isinstance(payload.get("name"), str) else None,
                    stats={
                        "total": coerce_int(stats.get("total")),
                        "passed": coerce_int(stats.get("passed")),
                        "failed": coerce_int(stats.get("failed")),
                        "flaky": coerce_int(stats.get("flaky")),
                        "broken": coerce_int(stats.get("broken")),
                    },
                    status=status if isinstance(status, str) else None,
                    duration=coerce_int(payload.get("duration")) or None,
                )
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                continue

        return ReportSummary()