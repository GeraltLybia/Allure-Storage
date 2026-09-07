/**
 * Dashboard view-model types re-exported from the single source of truth in
 * `src/types/reports.ts`. Kept as a module so existing panel imports stay
 * stable; do not redefine shapes here.
 */
export type {
  HistoryPoint,
  TrendPoint,
  HistoryTagHealth as TagHealth,
  HistoryFailureSignature as FailureSignature,
  HistoryUnstableTest as UnstableTest,
  HistoryStabilityDetailItem as StabilityDetailItem,
  HistoryStabilitySummary as StabilitySummary,
  HistoryAggregateStats as AggregateStats,
  HistorySelectedTestDetails as SelectedTestDetails,
  StabilityBucketKey,
  RecentReportItem,
  ProblemRunItem,
} from '../../../../types/reports'
