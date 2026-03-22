import tempfile
import unittest
from pathlib import Path

from app.services.reporting.analytics import HistoryAnalyticsService
from app.services.reporting.context import StorageContext
from app.services.reporting.models import (
    HistoryFilterOptions,
    HistoryIndexData,
    HistoryResultRecord,
    HistoryRunRecord,
)
from app.services.reporting.repositories.reports import ReportsRepository


class StubIndexService:
    @staticmethod
    def empty_filter_options() -> dict:
        return {"tags": [], "suites": [], "environments": []}


class ReportsRepositoryTests(unittest.TestCase):
    def test_list_report_entries_picks_nested_index_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            context = StorageContext(
                reports_folder=root / "reports",
                history_file=root / "history.jsonl",
                history_index_file=root / "history_index.json",
                max_reports=10,
            )
            repo = ReportsRepository(context)

            report_dir = repo.create_report_directory("report-1")
            nested_root = report_dir / "2026-03-22_run"
            nested_root.mkdir(parents=True)
            (nested_root / "index.html").write_text("<html></html>", encoding="utf-8")
            (nested_root / "summary.json").write_text(
                '{"name":"Nightly","duration":42,"status":"passed","stats":{"total":5,"passed":5}}',
                encoding="utf-8",
            )

            entries = repo.list_report_entries()

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].name, "Nightly")
            self.assertEqual(entries[0].entry_path, "report-1/2026-03-22_run/index.html")
            self.assertEqual(entries[0].stats["passed"], 5)


class AnalyticsTests(unittest.TestCase):
    def test_dashboard_aggregates_typed_index_records(self):
        analytics = HistoryAnalyticsService(StubIndexService())
        index = HistoryIndexData(
            version=1,
            source_size=10,
            source_mtime_ns=11,
            records=2,
            runs=[
                HistoryRunRecord(uuid="run-1", name="Run 1", timestamp=1000),
                HistoryRunRecord(uuid="run-2", name="Run 2", timestamp=2000),
            ],
            results=[
                HistoryResultRecord(
                    run_uuid="run-1",
                    run_name="Run 1",
                    timestamp=1000,
                    test_key="test-a",
                    name="test-a",
                    status="passed",
                    duration=10,
                    start=1,
                    stop=11,
                    environment="dev",
                    suite="api",
                    tags=["smoke"],
                    signature="Unknown failure",
                    message=None,
                ),
                HistoryResultRecord(
                    run_uuid="run-2",
                    run_name="Run 2",
                    timestamp=2000,
                    test_key="test-a",
                    name="test-a",
                    status="failed",
                    duration=20,
                    start=12,
                    stop=22,
                    environment="dev",
                    suite="api",
                    tags=["smoke"],
                    signature="AssertionError",
                    message="AssertionError",
                ),
            ],
            filter_options=HistoryFilterOptions(tags=["smoke"], suites=["api"], environments=["dev"]),
        )

        dashboard = analytics.get_dashboard(index=index, tags=["smoke"])
        details = analytics.get_test_details(index=index, test_key="test-a")

        self.assertEqual(dashboard["aggregateStats"]["total"], 2)
        self.assertEqual(dashboard["aggregateStats"]["failed"], 1)
        self.assertEqual(dashboard["stabilitySummary"]["flaky"], 1)
        self.assertEqual(dashboard["failureSignatures"][0]["signature"], "AssertionError")
        self.assertEqual(details["totalRuns"], 2)
        self.assertEqual(details["lastStatus"], "failed")

    def test_dashboard_filters_by_stop_timestamp_range(self):
        analytics = HistoryAnalyticsService(StubIndexService())
        index = HistoryIndexData(
            version=1,
            source_size=10,
            source_mtime_ns=11,
            records=3,
            runs=[
                HistoryRunRecord(uuid="run-1", name="Run 1", timestamp=1000),
                HistoryRunRecord(uuid="run-2", name="Run 2", timestamp=2000),
                HistoryRunRecord(uuid="run-3", name="Run 3", timestamp=3000),
            ],
            results=[
                HistoryResultRecord(
                    run_uuid="run-1",
                    run_name="Run 1",
                    timestamp=1000,
                    test_key="test-a",
                    name="test-a",
                    status="passed",
                    duration=10,
                    start=1,
                    stop=1000,
                    environment="dev",
                    suite="api",
                    tags=["smoke"],
                    signature="Unknown failure",
                    message=None,
                ),
                HistoryResultRecord(
                    run_uuid="run-2",
                    run_name="Run 2",
                    timestamp=2000,
                    test_key="test-a",
                    name="test-a",
                    status="failed",
                    duration=20,
                    start=12,
                    stop=2000,
                    environment="dev",
                    suite="api",
                    tags=["smoke"],
                    signature="AssertionError",
                    message="AssertionError",
                ),
                HistoryResultRecord(
                    run_uuid="run-3",
                    run_name="Run 3",
                    timestamp=3000,
                    test_key="test-b",
                    name="test-b",
                    status="passed",
                    duration=30,
                    start=23,
                    stop=None,
                    environment="dev",
                    suite="api",
                    tags=["regression"],
                    signature="Unknown failure",
                    message=None,
                ),
            ],
            filter_options=HistoryFilterOptions(
                tags=["regression", "smoke"],
                suites=["api"],
                environments=["dev"],
            ),
        )

        dashboard = analytics.get_dashboard(index=index, stop_from=1500, stop_to=2500)
        fallback_dashboard = analytics.get_dashboard(index=index, stop_from=2500, stop_to=3500)
        details = analytics.get_test_details(index=index, test_key="test-a", stop_from=1500, stop_to=2500)

        self.assertEqual(dashboard["aggregateStats"]["total"], 1)
        self.assertEqual(dashboard["aggregateStats"]["failed"], 1)
        self.assertEqual(dashboard["filteredRunCount"], 1)
        self.assertEqual(fallback_dashboard["aggregateStats"]["total"], 1)
        self.assertEqual(fallback_dashboard["filteredRunCount"], 1)
        self.assertIsNotNone(details)
        self.assertEqual(details["totalRuns"], 1)
        self.assertEqual(details["lastStatus"], "failed")


if __name__ == "__main__":
    unittest.main()
