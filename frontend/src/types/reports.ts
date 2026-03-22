export type ReportStats = {
  total: number
  passed: number
  failed: number
  flaky: number
  broken: number
}

export type Report = {
  id: string
  name: string
  created_at: string
  size: number
  entry_path?: string | null
  stats?: ReportStats | null
  status?: string | null
  duration?: number | null
}

export type HistoryInfo = {
  records: number
  updated_at: string | null
  size: number
}

export type HistoryLabel = {
  name: string
  value: string
}

export type HistoryTestResult = {
  id?: string
  name?: string
  fullName?: string
  environment?: string
  status?: string
  start?: number
  stop?: number
  duration?: number
  message?: string
  trace?: string
  labels?: HistoryLabel[]
  url?: string
  historyId?: string
  reportLinks?: string[]
}

export type HistoryRun = {
  uuid: string
  name: string
  timestamp: number
  knownTestCaseIds?: string[]
  testResults?: Record<string, HistoryTestResult>
  metrics?: Record<string, unknown>
  url?: string
}

export type HistoryAggregateStats = {
  total: number
  passed: number
  failed: number
  broken: number
  flaky: number
  other: number
}

export type HistoryFilterOptions = {
  tags: string[]
  suites: string[]
  environments: string[]
}

export type HistoryPoint = {
  key: string
  label: string
  total: number
  passed: number
  failed: number
  broken: number
  passRate: number
  reportName: string | null
}

export type HistoryTagHealth = {
  tag: string
  total: number
  incidents: number
  healthyRate: number
  passedRuns: number
  failedRuns: number
  brokenRuns: number
}

export type HistoryFailureSignature = {
  signature: string
  count: number
}

export type HistoryUnstableTest = {
  key: string
  name: string
  totalRuns: number
  incidents: number
  stability: number
  passedRuns: number
  failedRuns: number
  brokenRuns: number
  lastStatus: string
}

export type HistoryStabilityDetailItem = {
  key: string
  name: string
  lastStatus: string
  incidents: number
  totalRuns: number
}

export type HistoryStabilitySummary = {
  uniqueTests: number
  flaky: number
  alwaysFailed: number
  alwaysPassed: number
}

export type HistoryDashboardSummary = {
  filterOptions: HistoryFilterOptions
  filteredRunCount: number
  aggregateStats: HistoryAggregateStats
  p95Duration: number | null
  passRate: number
  incidentRate: number
  stabilitySummary: HistoryStabilitySummary
  stabilityDetails: {
    flaky: HistoryStabilityDetailItem[]
    alwaysFailed: HistoryStabilityDetailItem[]
    alwaysPassed: HistoryStabilityDetailItem[]
    incidents: HistoryStabilityDetailItem[]
  }
  trendPoints: HistoryPoint[]
  topUnstableTests: HistoryUnstableTest[]
  failureSignatures: HistoryFailureSignature[]
  tagHealth: HistoryTagHealth[]
}

export type HistorySelectedTestDetails = {
  name: string
  lastStatus: string
  totalRuns: number
  incidents: number
  history: HistoryTestResult[]
}
