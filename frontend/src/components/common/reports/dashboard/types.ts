import type { HistoryTestResult, Report } from '../../../../types/reports'

export type HistoryPoint = {
  key: string
  label: string
  total: number
  passed: number
  failed: number
  broken: number
  passRate: number
  reportId: string | null
}

export type TagHealth = {
  tag: string
  total: number
  incidents: number
  healthyRate: number
  passedRuns: number
  failedRuns: number
  brokenRuns: number
}

export type FailureSignature = {
  signature: string
  count: number
}

export type UnstableTest = {
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

export type StabilityBucketKey = 'flaky' | 'alwaysFailed' | 'alwaysPassed' | 'incidents'

export type StabilityDetailItem = {
  key: string
  name: string
  lastStatus: string
  incidents: number
  totalRuns: number
}

export type AggregateStats = {
  total: number
  passed: number
  failed: number
  broken: number
  flaky: number
  other: number
}

export type StabilitySummary = {
  uniqueTests: number
  flaky: number
  alwaysFailed: number
  alwaysPassed: number
}

export type RecentReportItem = {
  id: string
  label: string
  healthy: number
  incidents: number
  total: number
  selected: boolean
}

export type ProblemRunItem = {
  report: Report
  incidents: number
}

export type SelectedTestDetails = {
  name: string
  lastStatus: string
  totalRuns: number
  incidents: number
  history: HistoryTestResult[]
}
