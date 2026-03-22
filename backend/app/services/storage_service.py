import json
import re
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile


class StorageService:
    def __init__(
        self,
        reports_folder: Path,
        history_file: Path,
        history_index_file: Path,
        max_reports: int,
    ):
        self.reports_folder = reports_folder
        self.history_file = history_file
        self.history_index_file = history_index_file
        self.max_reports = max_reports
        self.reports_folder.mkdir(parents=True, exist_ok=True)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def list_reports(self) -> list[dict]:
        if not self.reports_folder.exists():
            return []

        reports: list[dict] = []
        for report_dir in self.reports_folder.iterdir():
            if not report_dir.is_dir():
                continue

            stat = report_dir.stat()
            size = sum(f.stat().st_size for f in report_dir.rglob("*") if f.is_file())
            report_root = self._resolve_report_root(report_dir)
            entry_path = self._build_entry_path(report_dir, report_root)
            summary = self._read_report_summary(report_dir, report_root)
            reports.append(
                {
                    "id": report_dir.name,
                    "name": summary.get("name") or report_dir.name,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": size,
                    "entry_path": entry_path,
                    "stats": summary.get("stats"),
                    "status": summary.get("status"),
                    "duration": summary.get("duration"),
                }
            )

        return sorted(reports, key=lambda x: x["created_at"], reverse=True)

    async def upload_report(self, file: UploadFile) -> dict:
        if not file.filename or not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")

        report_id = str(uuid.uuid4())
        report_path = self.reports_folder / report_id
        report_path.mkdir(parents=True, exist_ok=True)

        zip_path = report_path / "temp.zip"
        try:
            with zip_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            with zipfile.ZipFile(zip_path, "r") as archive:
                self._safe_extract_zip(archive, report_path)

            zip_path.unlink(missing_ok=True)
            self._apply_reports_retention()
            return {
                "id": report_id,
                "message": "Report uploaded and extracted successfully",
            }
        except zipfile.BadZipFile as exc:
            self._cleanup(report_path)
            raise HTTPException(status_code=400, detail="Invalid ZIP file") from exc
        except HTTPException:
            self._cleanup(report_path)
            raise
        except Exception as exc:
            self._cleanup(report_path)
            raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc
        finally:
            await file.close()

    def get_history_path(self) -> Path:
        if not self.history_file.exists():
            raise HTTPException(status_code=404, detail="History file not found")
        return self.history_file

    async def upload_history(self, file: UploadFile) -> dict:
        if not file.filename or not (
            file.filename.endswith(".jsonl") or file.filename.endswith(".json")
        ):
            raise HTTPException(status_code=400, detail="Only JSONL files are supported")

        temp_path = self.history_file.with_suffix(".upload.tmp")
        try:
            content = await file.read()
            self._validate_jsonl(content)
            temp_path.write_bytes(content)
            self._refresh_history_index(temp_path)
            temp_path.replace(self.history_file)
            return {"message": "History file updated successfully"}
        except json.JSONDecodeError as exc:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Invalid JSONL format") from exc
        except HTTPException:
            temp_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc
        finally:
            await file.close()

    def history_info(self) -> dict:
        if not self.history_file.exists():
            return {"records": 0, "updated_at": None, "size": 0}

        self._ensure_history_index()
        index = self._load_history_index()
        stat = self.history_file.stat()
        return {
            "records": self._coerce_int(index.get("records")),
            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size": stat.st_size,
        }

    def rebuild_history_index(self) -> dict:
        if not self.history_file.exists():
            raise HTTPException(status_code=404, detail="History file not found")

        self._write_history_index(self._build_history_index(self.history_file))
        return {"message": "History index rebuilt successfully"}

    def get_history_dashboard(
        self,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
    ) -> dict:
        if not self.history_file.exists():
            return self._empty_dashboard()

        self._ensure_history_index()
        index = self._load_history_index()
        filter_options = index.get("filter_options") or self._empty_filter_options()
        run_map = {
            run["uuid"]: run
            for run in index.get("runs", [])
            if isinstance(run, dict) and isinstance(run.get("uuid"), str)
        }

        aggregate_stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "broken": 0,
            "flaky": 0,
            "other": 0,
        }
        duration_values: list[int] = []
        filtered_runs: dict[str, dict] = {}
        history_by_test: dict[str, list[dict]] = {}
        failure_signature_counts: dict[str, int] = {}
        tag_counts: dict[str, dict[str, int]] = {}

        for result in index.get("results", []):
            if not isinstance(result, dict) or not self._result_matches_filters(
                result=result,
                tags=tags or [],
                suite=suite,
                environment=environment,
                signature=signature,
            ):
                continue

            status = self._normalize_status(result.get("status"))
            aggregate_stats["total"] += 1
            if status == "passed":
                aggregate_stats["passed"] += 1
            elif status == "failed":
                aggregate_stats["failed"] += 1
            elif status == "broken":
                aggregate_stats["broken"] += 1
            elif status == "flaky":
                aggregate_stats["flaky"] += 1
            else:
                aggregate_stats["other"] += 1

            duration = result.get("duration")
            if isinstance(duration, int):
                duration_values.append(duration)

            run_uuid = result.get("runUuid")
            if isinstance(run_uuid, str):
                run_info = run_map.get(run_uuid) or {
                    "uuid": run_uuid,
                    "name": result.get("runName") or run_uuid,
                    "timestamp": self._coerce_int(result.get("timestamp")),
                }
                bucket = filtered_runs.setdefault(
                    run_uuid,
                    {
                        "uuid": run_info["uuid"],
                        "name": run_info.get("name") or run_uuid,
                        "timestamp": self._coerce_int(run_info.get("timestamp")),
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "broken": 0,
                    },
                )
                bucket["total"] += 1
                if status == "passed":
                    bucket["passed"] += 1
                elif status == "failed":
                    bucket["failed"] += 1
                elif status == "broken":
                    bucket["broken"] += 1

            test_key = result.get("testKey")
            if isinstance(test_key, str):
                history_by_test.setdefault(test_key, []).append(result)

            if status in {"failed", "broken"}:
                failure_signature = result.get("signature") or "Unknown failure"
                failure_signature_counts[failure_signature] = (
                    failure_signature_counts.get(failure_signature, 0) + 1
                )

            for tag in result.get("tags", []):
                if not isinstance(tag, str):
                    continue
                tag_bucket = tag_counts.setdefault(
                    tag,
                    {
                        "total": 0,
                        "incidents": 0,
                        "passedRuns": 0,
                        "failedRuns": 0,
                        "brokenRuns": 0,
                    },
                )
                tag_bucket["total"] += 1
                if status == "passed":
                    tag_bucket["passedRuns"] += 1
                if status == "failed":
                    tag_bucket["failedRuns"] += 1
                    tag_bucket["incidents"] += 1
                if status == "broken":
                    tag_bucket["brokenRuns"] += 1
                    tag_bucket["incidents"] += 1

        duration_values.sort()
        p95_duration = self._percentile(duration_values, 95)
        pass_rate = (
            round((aggregate_stats["passed"] / aggregate_stats["total"]) * 100)
            if aggregate_stats["total"]
            else 0
        )
        incidents = aggregate_stats["failed"] + aggregate_stats["broken"]
        incident_rate = (
            round((incidents / aggregate_stats["total"]) * 100)
            if aggregate_stats["total"]
            else 0
        )

        stability_summary = {
            "uniqueTests": len(history_by_test),
            "flaky": 0,
            "alwaysFailed": 0,
            "alwaysPassed": 0,
        }
        stability_details = {
            "flaky": [],
            "alwaysFailed": [],
            "alwaysPassed": [],
            "incidents": [],
        }
        top_unstable_tests: list[dict] = []

        for key, results in history_by_test.items():
            summary = self._build_test_summary(key, results)
            statuses = summary["statuses"]
            has_incident = "failed" in statuses or "broken" in statuses
            has_passed = "passed" in statuses
            detail_item = {
                "key": key,
                "name": summary["name"],
                "lastStatus": summary["last_status"],
                "incidents": summary["incidents"],
                "totalRuns": summary["total_runs"],
            }

            if has_incident:
                stability_details["incidents"].append(detail_item)
            if has_incident and has_passed:
                stability_summary["flaky"] += 1
                stability_details["flaky"].append(detail_item)
            if has_incident and not has_passed:
                stability_summary["alwaysFailed"] += 1
                stability_details["alwaysFailed"].append(detail_item)
            if statuses == {"passed"}:
                stability_summary["alwaysPassed"] += 1
                stability_details["alwaysPassed"].append(detail_item)

            if summary["total_runs"] > 1 and summary["incidents"] > 0:
                top_unstable_tests.append(
                    {
                        "key": key,
                        "name": summary["name"],
                        "totalRuns": summary["total_runs"],
                        "incidents": summary["incidents"],
                        "stability": (
                            round(
                                ((summary["total_runs"] - summary["incidents"]) / summary["total_runs"])
                                * 100
                            )
                            if summary["total_runs"]
                            else 0
                        ),
                        "passedRuns": summary["passed_runs"],
                        "failedRuns": summary["failed_runs"],
                        "brokenRuns": summary["broken_runs"],
                        "lastStatus": summary["last_status"],
                    }
                )

        detail_sorter = lambda item: (-item["incidents"], item["name"])
        for bucket in stability_details.values():
            bucket.sort(key=detail_sorter)

        top_unstable_tests.sort(
            key=lambda item: (
                item["stability"],
                -item["incidents"],
                -item["totalRuns"],
            )
        )

        trend_points = sorted(filtered_runs.values(), key=lambda item: item["timestamp"])[-8:]
        trend_points = [
            {
                "key": run["uuid"],
                "label": self._build_run_label(run.get("name"), run.get("timestamp"), run["uuid"]),
                "total": run["total"],
                "passed": run["passed"],
                "failed": run["failed"],
                "broken": run["broken"],
                "passRate": round((run["passed"] / run["total"]) * 100) if run["total"] else 0,
                "reportName": run.get("name"),
            }
            for run in trend_points
        ]

        failure_signatures = [
            {"signature": signature_value, "count": count}
            for signature_value, count in sorted(
                failure_signature_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[:5]
        ]

        tag_health = [
            {
                "tag": tag,
                "total": value["total"],
                "incidents": value["incidents"],
                "healthyRate": (
                    round(((value["total"] - value["incidents"]) / value["total"]) * 100)
                    if value["total"]
                    else 0
                ),
                "passedRuns": value["passedRuns"],
                "failedRuns": value["failedRuns"],
                "brokenRuns": value["brokenRuns"],
            }
            for tag, value in sorted(
                tag_counts.items(),
                key=lambda item: (-item[1]["incidents"], item[0]),
            )[:5]
        ]

        return {
            "filterOptions": filter_options,
            "filteredRunCount": len(filtered_runs),
            "aggregateStats": aggregate_stats,
            "p95Duration": p95_duration,
            "passRate": pass_rate,
            "incidentRate": incident_rate,
            "stabilitySummary": stability_summary,
            "stabilityDetails": stability_details,
            "trendPoints": trend_points,
            "topUnstableTests": top_unstable_tests[:6],
            "failureSignatures": failure_signatures,
            "tagHealth": tag_health,
        }

    def get_history_test_details(
        self,
        test_key: str,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
    ) -> dict | None:
        if not self.history_file.exists():
            return None

        self._ensure_history_index()
        index = self._load_history_index()
        matches = [
            result
            for result in index.get("results", [])
            if isinstance(result, dict)
            and result.get("testKey") == test_key
            and self._result_matches_filters(
                result=result,
                tags=tags or [],
                suite=suite,
                environment=environment,
                signature=signature,
            )
        ]

        if not matches:
            return None

        ordered = sorted(matches, key=lambda result: self._coerce_int(result.get("stop")), reverse=True)
        latest = ordered[0]
        incidents = sum(
            1
            for result in ordered
            if self._normalize_status(result.get("status")) in {"failed", "broken"}
        )
        return {
            "name": latest.get("name") or test_key,
            "lastStatus": self._normalize_status(latest.get("status")),
            "totalRuns": len(ordered),
            "incidents": incidents,
            "history": [
                {
                    "status": result.get("status"),
                    "duration": result.get("duration"),
                    "environment": result.get("environment"),
                    "message": result.get("message"),
                    "start": result.get("start"),
                }
                for result in ordered[:8]
            ],
        }

    def delete_report(self, report_id: str) -> dict:
        report_path = self.reports_folder / report_id
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        try:
            shutil.rmtree(report_path)
            return {"message": "Report deleted successfully"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Delete failed: {exc}") from exc

    def create_report_archive(self, report_id: str) -> tuple[Path, str]:
        report_path = self.reports_folder / report_id
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        zip_path = self.reports_folder / f"{report_id}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", report_path)
        return zip_path, f"{report_id}.zip"

    def _ensure_history_index(self) -> None:
        if not self.history_file.exists():
            return

        if not self.history_index_file.exists():
            self._write_history_index(self._build_history_index(self.history_file))
            return

        try:
            index = self._load_history_index()
        except HTTPException:
            self._write_history_index(self._build_history_index(self.history_file))
            return

        history_stat = self.history_file.stat()
        source_size = self._coerce_int(index.get("source_size"))
        source_mtime_ns = self._coerce_int(index.get("source_mtime_ns"))

        if source_size == history_stat.st_size and source_mtime_ns == history_stat.st_mtime_ns:
            return

        if history_stat.st_size > source_size and source_size >= 0:
            self._append_index_from_offset(index, self.history_file, source_size)
            self._write_history_index(index)
            return

        self._write_history_index(self._build_history_index(self.history_file))

    def _refresh_history_index(self, new_history_path: Path) -> None:
        if not self.history_file.exists() or not self.history_index_file.exists():
            self._write_history_index(self._build_history_index(new_history_path))
            return

        index = self._load_history_index()
        old_size = self._coerce_int(index.get("source_size"))
        if new_history_path.stat().st_size >= old_size and self._files_share_prefix(
            self.history_file, new_history_path, old_size
        ):
            self._append_index_from_offset(index, new_history_path, old_size)
            self._write_history_index(index)
            return

        self._write_history_index(self._build_history_index(new_history_path))

    def _build_history_index(self, source_path: Path) -> dict:
        index = {
            "version": 1,
            "source_size": source_path.stat().st_size,
            "source_mtime_ns": source_path.stat().st_mtime_ns,
            "records": 0,
            "runs": [],
            "results": [],
            "filter_options": self._empty_filter_options(),
        }
        self._append_index_from_offset(index, source_path, 0)
        return index

    def _append_index_from_offset(self, index: dict, source_path: Path, offset: int) -> None:
        run_ids = {
            run["uuid"]
            for run in index.get("runs", [])
            if isinstance(run, dict) and isinstance(run.get("uuid"), str)
        }
        results = index.setdefault("results", [])
        runs = index.setdefault("runs", [])
        filter_options = index.get("filter_options") or self._empty_filter_options()
        tags = set(filter_options.get("tags", []))
        suites = set(filter_options.get("suites", []))
        environments = set(filter_options.get("environments", []))
        records = self._coerce_int(index.get("records"))

        with source_path.open("r", encoding="utf-8") as source:
            if offset:
                source.seek(offset)
            for raw_line in source:
                line = raw_line.strip()
                if not line:
                    continue
                run = json.loads(line)
                records += 1
                run_uuid = run.get("uuid")
                run_name = run.get("name") or run_uuid
                run_timestamp = self._coerce_int(run.get("timestamp"))

                if isinstance(run_uuid, str) and run_uuid not in run_ids:
                    runs.append(
                        {
                            "uuid": run_uuid,
                            "name": run_name,
                            "timestamp": run_timestamp,
                        }
                    )
                    run_ids.add(run_uuid)

                for result in (run.get("testResults") or {}).values():
                    compact = self._compact_history_result(result, run_uuid, run_name, run_timestamp)
                    results.append(compact)
                    tags.update(compact["tags"])
                    if compact["suite"]:
                        suites.add(compact["suite"])
                    environments.add(compact["environment"])

        index["records"] = records
        stat = source_path.stat()
        index["source_size"] = stat.st_size
        index["source_mtime_ns"] = stat.st_mtime_ns
        index["filter_options"] = {
            "tags": sorted(tags),
            "suites": sorted(suites),
            "environments": sorted(environments),
        }

    def _load_history_index(self) -> dict:
        try:
            return json.loads(self.history_index_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise HTTPException(status_code=500, detail=f"History index is invalid: {exc}") from exc

    def _write_history_index(self, index: dict) -> None:
        temp_path = self.history_index_file.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(index, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temp_path.replace(self.history_index_file)

    def _compact_history_result(
        self,
        result: dict,
        run_uuid: str | None,
        run_name: str | None,
        run_timestamp: int,
    ) -> dict:
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
        environment_value = environment.strip() if isinstance(environment, str) and environment.strip() else "unknown"
        test_key = (
            result.get("fullName")
            or result.get("name")
            or result.get("historyId")
            or result.get("id")
            or str(uuid.uuid4())
        )
        return {
            "runUuid": run_uuid,
            "runName": run_name,
            "timestamp": run_timestamp,
            "testKey": test_key,
            "name": result.get("fullName") or result.get("name") or test_key,
            "status": result.get("status"),
            "duration": self._coerce_optional_int(result.get("duration")),
            "start": self._coerce_optional_int(result.get("start")),
            "stop": self._coerce_optional_int(result.get("stop")),
            "environment": environment_value,
            "suite": suite if isinstance(suite, str) and suite else "unknown",
            "tags": tags,
            "signature": self._build_signature(result),
            "message": self._extract_message(result),
        }

    def _build_test_summary(self, key: str, results: list[dict]) -> dict:
        latest = max(results, key=lambda item: self._coerce_int(item.get("stop")))
        statuses = {self._normalize_status(result.get("status")) for result in results}
        passed_runs = sum(
            1 for result in results if self._normalize_status(result.get("status")) == "passed"
        )
        failed_runs = sum(
            1 for result in results if self._normalize_status(result.get("status")) == "failed"
        )
        broken_runs = sum(
            1 for result in results if self._normalize_status(result.get("status")) == "broken"
        )
        incidents = failed_runs + broken_runs
        return {
            "name": latest.get("name") or key,
            "last_status": self._normalize_status(latest.get("status")),
            "statuses": statuses,
            "total_runs": len(results),
            "passed_runs": passed_runs,
            "failed_runs": failed_runs,
            "broken_runs": broken_runs,
            "incidents": incidents,
        }

    def _result_matches_filters(
        self,
        result: dict,
        tags: list[str],
        suite: str | None,
        environment: str | None,
        signature: str | None,
    ) -> bool:
        result_tags = result.get("tags", [])
        tag_matches = not tags or any(tag in result_tags for tag in tags)
        suite_matches = not suite or suite == "all" or result.get("suite") == suite
        environment_matches = (
            not environment
            or environment == "all"
            or result.get("environment") == environment
        )
        status = self._normalize_status(result.get("status"))
        signature_matches = (
            not signature
            or signature == "all"
            or (
                status in {"failed", "broken"}
                and (result.get("signature") or "Unknown failure") == signature
            )
        )
        return tag_matches and suite_matches and environment_matches and signature_matches

    def _build_run_label(self, name: object, timestamp: object, fallback: str) -> str:
        if isinstance(name, str) and name.strip():
            return name
        try:
            date = datetime.fromtimestamp(self._coerce_int(timestamp) / 1000)
            return date.isoformat(sep=" ", timespec="minutes")
        except Exception:
            return fallback

    def _build_signature(self, result: dict) -> str:
        message = result.get("message")
        if isinstance(message, str) and message.strip():
            line = message.split("\n", 1)[0].strip()
            return f"{line[:90]}…" if len(line) > 90 else line
        trace = result.get("trace")
        if isinstance(trace, str) and trace.strip():
            line = trace.split("\n", 1)[0].strip()
            return f"{line[:90]}…" if len(line) > 90 else line
        return "Unknown failure"

    def _extract_message(self, result: dict) -> str | None:
        message = result.get("message")
        if isinstance(message, str) and message.strip():
            return message.split("\n", 1)[0].strip()
        trace = result.get("trace")
        if isinstance(trace, str) and trace.strip():
            return trace.split("\n", 1)[0].strip()
        return None

    def _normalize_status(self, value: object) -> str:
        return value.strip().lower() if isinstance(value, str) and value.strip() else "unknown"

    def _files_share_prefix(self, left: Path, right: Path, size: int) -> bool:
        if size <= 0:
            return True
        chunk_size = 1024 * 1024
        with left.open("rb") as left_file, right.open("rb") as right_file:
            remaining = size
            while remaining > 0:
                current_chunk = min(chunk_size, remaining)
                if left_file.read(current_chunk) != right_file.read(current_chunk):
                    return False
                remaining -= current_chunk
        return True

    def _percentile(self, values: list[int], q: int) -> int | None:
        if not values:
            return None
        index = min(len(values) - 1, round((q / 100) * (len(values) - 1)))
        return values[index]

    def _empty_filter_options(self) -> dict:
        return {"tags": [], "suites": [], "environments": []}

    def _empty_dashboard(self) -> dict:
        return {
            "filterOptions": self._empty_filter_options(),
            "filteredRunCount": 0,
            "aggregateStats": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "broken": 0,
                "flaky": 0,
                "other": 0,
            },
            "p95Duration": None,
            "passRate": 0,
            "incidentRate": 0,
            "stabilitySummary": {
                "uniqueTests": 0,
                "flaky": 0,
                "alwaysFailed": 0,
                "alwaysPassed": 0,
            },
            "stabilityDetails": {
                "flaky": [],
                "alwaysFailed": [],
                "alwaysPassed": [],
                "incidents": [],
            },
            "trendPoints": [],
            "topUnstableTests": [],
            "failureSignatures": [],
            "tagHealth": [],
        }

    def _resolve_report_root(self, report_dir: Path) -> Path | None:
        index_in_root = report_dir / "index.html"
        if index_in_root.exists():
            return report_dir

        candidates: list[Path] = []
        for index_path in report_dir.rglob("index.html"):
            if "__MACOSX" in index_path.parts:
                continue
            candidates.append(index_path.parent)

        if not candidates:
            return None

        candidates.sort(
            key=lambda path: (
                0 if self._is_date_like_dir(path.name) else 1,
                len(path.relative_to(report_dir).parts),
                path.as_posix(),
            )
        )
        return candidates[0]

    def _build_entry_path(self, report_dir: Path, report_root: Path | None) -> str | None:
        if report_root is None:
            return None
        relative_root = report_root.relative_to(report_dir)
        if not relative_root.parts:
            return f"{report_dir.name}/index.html"
        return f"{report_dir.name}/{relative_root.as_posix()}/index.html"

    def _validate_jsonl(self, content: bytes) -> None:
        lines = content.decode("utf-8").strip().split("\n")
        for line in lines:
            if line.strip():
                json.loads(line)

    def _read_report_summary(self, report_dir: Path, report_root: Path | None) -> dict:
        candidates: list[Path] = []
        if report_root is not None:
            candidates.append(report_root / "summary.json")
        candidates.append(report_dir / "summary.json")
        for summary_path in report_dir.rglob("summary.json"):
            if "__MACOSX" in summary_path.parts:
                continue
            if summary_path not in candidates:
                candidates.append(summary_path)

        for summary_path in candidates:
            if not summary_path.exists() or not summary_path.is_file():
                continue

            try:
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
                stats = payload.get("stats") or {}
                total = self._coerce_int(stats.get("total"))
                passed = self._coerce_int(stats.get("passed"))
                failed = self._coerce_int(stats.get("failed"))
                flaky = self._coerce_int(stats.get("flaky"))
                broken = self._coerce_int(stats.get("broken"))
                duration = self._coerce_int(payload.get("duration"))
                status = payload.get("status")

                return {
                    "name": payload.get("name"),
                    "stats": {
                        "total": total,
                        "passed": passed,
                        "failed": failed,
                        "flaky": flaky,
                        "broken": broken,
                    },
                    "status": status if isinstance(status, str) else None,
                    "duration": duration,
                }
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                continue

        return {}

    def _is_date_like_dir(self, value: str) -> bool:
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}([_-].+)?$", value))

    def _coerce_int(self, value: object) -> int:
        if isinstance(value, bool):
            return 0
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _coerce_optional_int(self, value: object) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _safe_extract_zip(self, archive: zipfile.ZipFile, destination: Path) -> None:
        destination_resolved = destination.resolve()

        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            if destination_resolved not in member_path.parents and member_path != destination_resolved:
                raise HTTPException(status_code=400, detail="Archive contains invalid paths")

        archive.extractall(destination)

    def _cleanup(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path)

    def _apply_reports_retention(self) -> None:
        report_dirs = [path for path in self.reports_folder.iterdir() if path.is_dir()]
        if len(report_dirs) <= self.max_reports:
            return

        report_dirs.sort(key=lambda path: path.stat().st_ctime)
        for old_report_dir in report_dirs[: len(report_dirs) - self.max_reports]:
            shutil.rmtree(old_report_dir)
