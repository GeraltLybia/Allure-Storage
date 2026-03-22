from pydantic import BaseModel


class HistoryInfo(BaseModel):
    records: int
    updated_at: str | None
    size: int


class HistoryFilterOptions(BaseModel):
    tags: list[str]
    suites: list[str]
    environments: list[str]


class HistoryAggregateStats(BaseModel):
    total: int
    passed: int
    failed: int
    broken: int
    flaky: int
    other: int


class HistoryStabilitySummary(BaseModel):
    uniqueTests: int
    flaky: int
    alwaysFailed: int
    alwaysPassed: int


class HistoryFailureSignature(BaseModel):
    signature: str
    count: int


class HistoryTagHealth(BaseModel):
    tag: str
    total: int
    incidents: int
    healthyRate: int
    passedRuns: int
    failedRuns: int
    brokenRuns: int


class HistoryPoint(BaseModel):
    key: str
    label: str
    total: int
    passed: int
    failed: int
    broken: int
    passRate: int
    reportName: str | None


class HistoryUnstableTest(BaseModel):
    key: str
    name: str
    totalRuns: int
    incidents: int
    stability: int
    passedRuns: int
    failedRuns: int
    brokenRuns: int
    lastStatus: str


class HistoryStabilityDetailItem(BaseModel):
    key: str
    name: str
    lastStatus: str
    incidents: int
    totalRuns: int


class HistoryStabilityDetails(BaseModel):
    flaky: list[HistoryStabilityDetailItem]
    alwaysFailed: list[HistoryStabilityDetailItem]
    alwaysPassed: list[HistoryStabilityDetailItem]
    incidents: list[HistoryStabilityDetailItem]


class HistoryDashboardSummary(BaseModel):
    filterOptions: HistoryFilterOptions
    filteredRunCount: int
    aggregateStats: HistoryAggregateStats
    p95Duration: int | None
    passRate: int
    incidentRate: int
    stabilitySummary: HistoryStabilitySummary
    stabilityDetails: HistoryStabilityDetails
    trendPoints: list[HistoryPoint]
    topUnstableTests: list[HistoryUnstableTest]
    failureSignatures: list[HistoryFailureSignature]
    tagHealth: list[HistoryTagHealth]


class HistoryTestDetailsEntry(BaseModel):
    status: str | None = None
    duration: int | None = None
    environment: str | None = None
    message: str | None = None
    start: int | None = None


class HistorySelectedTestDetails(BaseModel):
    name: str
    lastStatus: str
    totalRuns: int
    incidents: int
    history: list[HistoryTestDetailsEntry]
