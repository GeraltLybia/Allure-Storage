from .common import build_run_label, normalize_status, percentile
from .models import HistoryIndexData, HistoryResultRecord


class HistoryAnalyticsService:
    def __init__(self, index_service):
        self.index_service = index_service

    def get_dashboard(
        self,
        index: HistoryIndexData,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
        stop_from: int | None = None,
        stop_to: int | None = None,
    ) -> dict:
        filter_options = index.filter_options.to_dict()
        run_map = {run.uuid: run for run in index.runs}

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
        history_by_test: dict[str, list[HistoryResultRecord]] = {}
        failure_signature_counts: dict[str, int] = {}
        tag_counts: dict[str, dict[str, int]] = {}

        for result in index.results:
            if not self.result_matches_filters(
                result=result,
                tags=tags or [],
                suite=suite,
                environment=environment,
                signature=signature,
                stop_from=stop_from,
                stop_to=stop_to,
            ):
                continue

            status = normalize_status(result.status)
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

            if isinstance(result.duration, int):
                duration_values.append(result.duration)

            if isinstance(result.run_uuid, str):
                run_info = run_map.get(result.run_uuid)
                run_name = run_info.name if run_info else result.run_name or result.run_uuid
                run_timestamp = run_info.timestamp if run_info else result.timestamp
                bucket = filtered_runs.setdefault(
                    result.run_uuid,
                    {
                        "uuid": result.run_uuid,
                        "name": run_name,
                        "timestamp": run_timestamp,
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

            history_by_test.setdefault(result.test_key, []).append(result)

            if status in {"failed", "broken"}:
                failure_signature = result.signature or "Unknown failure"
                failure_signature_counts[failure_signature] = (
                    failure_signature_counts.get(failure_signature, 0) + 1
                )

            for tag in result.tags:
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
        p95_duration = percentile(duration_values, 95)
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
            summary = self.build_test_summary(key, results)
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
                "label": build_run_label(run.get("name"), run.get("timestamp"), run["uuid"]),
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

    def get_test_details(
        self,
        index: HistoryIndexData,
        test_key: str,
        tags: list[str] | None = None,
        suite: str | None = None,
        environment: str | None = None,
        signature: str | None = None,
        stop_from: int | None = None,
        stop_to: int | None = None,
    ) -> dict | None:
        matches = [
            result
            for result in index.results
            if result.test_key == test_key
            and self.result_matches_filters(
                result=result,
                tags=tags or [],
                suite=suite,
                environment=environment,
                signature=signature,
                stop_from=stop_from,
                stop_to=stop_to,
            )
        ]

        if not matches:
            return None

        ordered = sorted(matches, key=lambda result: result.stop or 0, reverse=True)
        latest = ordered[0]
        incidents = sum(
            1 for result in ordered if normalize_status(result.status) in {"failed", "broken"}
        )
        return {
            "name": latest.name or test_key,
            "lastStatus": normalize_status(latest.status),
            "totalRuns": len(ordered),
            "incidents": incidents,
            "history": [
                {
                    "status": result.status,
                    "duration": result.duration,
                    "environment": result.environment,
                    "message": result.message,
                    "start": result.start,
                }
                for result in ordered[:8]
            ],
        }

    def build_test_summary(self, key: str, results: list[HistoryResultRecord]) -> dict:
        latest = max(results, key=lambda item: item.stop or 0)
        statuses = {normalize_status(result.status) for result in results}
        passed_runs = sum(1 for result in results if normalize_status(result.status) == "passed")
        failed_runs = sum(1 for result in results if normalize_status(result.status) == "failed")
        broken_runs = sum(1 for result in results if normalize_status(result.status) == "broken")
        incidents = failed_runs + broken_runs
        return {
            "name": latest.name or key,
            "last_status": normalize_status(latest.status),
            "statuses": statuses,
            "total_runs": len(results),
            "passed_runs": passed_runs,
            "failed_runs": failed_runs,
            "broken_runs": broken_runs,
            "incidents": incidents,
        }

    def result_matches_filters(
        self,
        result: HistoryResultRecord,
        tags: list[str],
        suite: str | None,
        environment: str | None,
        signature: str | None,
        stop_from: int | None,
        stop_to: int | None,
    ) -> bool:
        tag_matches = not tags or any(tag in result.tags for tag in tags)
        suite_matches = not suite or suite == "all" or result.suite == suite
        environment_matches = (
            not environment or environment == "all" or result.environment == environment
        )
        status = normalize_status(result.status)
        signature_matches = (
            not signature
            or signature == "all"
            or (
                status in {"failed", "broken"}
                and (result.signature or "Unknown failure") == signature
            )
        )
        stop_timestamp = self.resolve_result_timestamp(result)
        stop_from_matches = stop_from is None or stop_timestamp >= stop_from
        stop_to_matches = stop_to is None or stop_timestamp <= stop_to
        return (
            tag_matches
            and suite_matches
            and environment_matches
            and signature_matches
            and stop_from_matches
            and stop_to_matches
        )

    @staticmethod
    def resolve_result_timestamp(result: HistoryResultRecord) -> int:
        if isinstance(result.stop, int) and result.stop > 0:
            return result.stop
        if isinstance(result.timestamp, int) and result.timestamp > 0:
            return result.timestamp
        return 0

    def empty_dashboard(self) -> dict:
        return {
            "filterOptions": self.index_service.empty_filter_options(),
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
