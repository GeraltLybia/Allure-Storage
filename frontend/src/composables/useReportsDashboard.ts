import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { HistoryRun, HistoryTestResult, Report } from '../types/reports'
import type {
  FailureSignature,
  HistoryPoint,
  ProblemRunItem,
  SelectedTestDetails,
  StabilityBucketKey,
  StabilityDetailItem,
  TagHealth,
  UnstableTest,
  RecentReportItem,
} from '../components/common/reports/dashboard/types'

export function useReportsDashboard(props: {
  reports: Report[]
  historyRuns: HistoryRun[]
  selectedReportId: string | null
  getReportTitle: (report: Report) => string | undefined
}) {
  const route = useRoute()
  const router = useRouter()

  const activeTags = ref<string[]>([])
  const activeSuite = ref('all')
  const activeEnvironment = ref('all')
  const activeSignature = ref('all')
  const activeStabilityBucket = ref<StabilityBucketKey | null>(null)
  const stabilitySearch = ref('')
  const selectedTestKey = ref<string | null>(null)

  function toTimestamp(value: string) {
    const timestamp = new Date(value).getTime()
    return Number.isFinite(timestamp) ? timestamp : 0
  }

  function openReport(id: string) {
    router.push({ name: 'report-by-id', params: { reportId: id } })
  }

  function parseQueryList(value: unknown) {
    if (typeof value !== 'string') return []
    return value.split(',').map((item) => item.trim()).filter(Boolean)
  }

  function arraysEqual(left: string[], right: string[]) {
    if (left.length !== right.length) return false
    return left.every((item, index) => item === right[index])
  }

  function toggleTag(tag: string) {
    activeTags.value = activeTags.value.includes(tag)
      ? activeTags.value.filter((item) => item !== tag)
      : [...activeTags.value, tag].sort((left, right) => left.localeCompare(right))
  }

  function toggleSignature(signature: string) {
    activeSignature.value = activeSignature.value === signature ? 'all' : signature
  }

  function normalizeStatus(value: string | undefined) {
    return value?.trim().toLowerCase() ?? 'unknown'
  }

  function buildSignature(result: HistoryTestResult) {
    const base = result.message?.split('\n')[0]?.trim() || result.trace?.split('\n')[0]?.trim()
    if (!base) return 'Unknown failure'
    return base.length > 90 ? `${base.slice(0, 90)}…` : base
  }

  function buildRunLabel(run: HistoryRun) {
    if (run.name?.trim()) return run.name
    const date = new Date(run.timestamp)
    return Number.isNaN(date.getTime()) ? run.uuid : date.toLocaleString()
  }

  function resultMatchesFilters(result: HistoryTestResult) {
    const labels = result.labels ?? []
    const tagValues = labels.filter((label) => label.name === 'tag').map((label) => label.value)
    const suiteValue =
      labels.find((label) => label.name === 'suite')?.value ||
      labels.find((label) => label.name === 'parentSuite')?.value ||
      'unknown'
    const environmentValue = result.environment?.trim() || 'unknown'

    const tagMatches =
      activeTags.value.length === 0 || activeTags.value.some((tag) => tagValues.includes(tag))
    const suiteMatches = activeSuite.value === 'all' || suiteValue === activeSuite.value
    const environmentMatches =
      activeEnvironment.value === 'all' || environmentValue === activeEnvironment.value
    const signatureMatches =
      activeSignature.value === 'all' ||
      ((normalizeStatus(result.status) === 'failed' || normalizeStatus(result.status) === 'broken') &&
        buildSignature(result) === activeSignature.value)

    return tagMatches && suiteMatches && environmentMatches && signatureMatches
  }

  const reportMapByName = computed(() => {
    const map = new Map<string, string>()
    for (const report of props.reports) {
      const keys = [report.name, props.getReportTitle(report)].filter(
        (value): value is string => Boolean(value?.trim()),
      )
      for (const key of keys) map.set(key, report.id)
    }
    return map
  })

  const filterOptions = computed(() => {
    const tags = new Set<string>()
    const suites = new Set<string>()
    const environments = new Set<string>()

    for (const run of props.historyRuns) {
      for (const result of Object.values(run.testResults ?? {})) {
        for (const label of result.labels ?? []) {
          if (label.name === 'tag' && label.value) tags.add(label.value)
          if ((label.name === 'suite' || label.name === 'parentSuite') && label.value) suites.add(label.value)
        }
        environments.add(result.environment?.trim() || 'unknown')
      }
    }

    return {
      tags: Array.from(tags).sort((left, right) => left.localeCompare(right)),
      suites: Array.from(suites).sort((left, right) => left.localeCompare(right)),
      environments: Array.from(environments).sort((left, right) => left.localeCompare(right)),
    }
  })

  watch(
    () => route.query,
    (query) => {
      const nextTags = parseQueryList(query.tags).sort((left, right) => left.localeCompare(right))
      const nextSuite = typeof query.suite === 'string' ? query.suite : 'all'
      const nextEnvironment = typeof query.environment === 'string' ? query.environment : 'all'
      const nextSignature = typeof query.signature === 'string' ? query.signature : 'all'

      if (!arraysEqual(activeTags.value, nextTags)) activeTags.value = nextTags
      activeSuite.value = nextSuite
      activeEnvironment.value = nextEnvironment
      activeSignature.value = nextSignature
    },
    { immediate: true },
  )

  watch([activeTags, activeSuite, activeEnvironment, activeSignature], () => {
    const nextQuery: Record<string, string> = {}
    if (activeTags.value.length) nextQuery.tags = activeTags.value.join(',')
    if (activeSuite.value !== 'all') nextQuery.suite = activeSuite.value
    if (activeEnvironment.value !== 'all') nextQuery.environment = activeEnvironment.value
    if (activeSignature.value !== 'all') nextQuery.signature = activeSignature.value

    const currentTags = parseQueryList(route.query.tags).sort((left, right) => left.localeCompare(right))
    const currentSuite = typeof route.query.suite === 'string' ? route.query.suite : 'all'
    const currentEnvironment = typeof route.query.environment === 'string' ? route.query.environment : 'all'
    const currentSignature = typeof route.query.signature === 'string' ? route.query.signature : 'all'

    if (
      arraysEqual(currentTags, activeTags.value) &&
      currentSuite === activeSuite.value &&
      currentEnvironment === activeEnvironment.value &&
      currentSignature === activeSignature.value
    ) {
      return
    }

    router.replace({ query: nextQuery })
  })

  const filteredHistoryRuns = computed(() =>
    props.historyRuns
      .map((run) => ({
        ...run,
        testResults: Object.fromEntries(
          Object.entries(run.testResults ?? {}).filter(([, result]) => resultMatchesFilters(result)),
        ),
      }))
      .filter((run) => Object.keys(run.testResults ?? {}).length > 0),
  )

  const historyResults = computed(() =>
    filteredHistoryRuns.value.flatMap((run) => Object.values(run.testResults ?? {})),
  )

  const aggregateStats = computed(() =>
    historyResults.value.reduce(
      (accumulator, result) => {
        const status = normalizeStatus(result.status)
        accumulator.total += 1
        if (status === 'passed') accumulator.passed += 1
        else if (status === 'failed') accumulator.failed += 1
        else if (status === 'broken') accumulator.broken += 1
        else if (status === 'flaky') accumulator.flaky += 1
        else accumulator.other += 1
        return accumulator
      },
      { total: 0, passed: 0, failed: 0, broken: 0, flaky: 0, other: 0 },
    ),
  )

  const durationValues = computed(() =>
    historyResults.value
      .map((result) => result.duration)
      .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
      .sort((left, right) => left - right),
  )

  function percentile(values: number[], q: number) {
    if (!values.length) return null
    const index = Math.min(values.length - 1, Math.round((q / 100) * (values.length - 1)))
    return values[index] ?? null
  }

  const p95Duration = computed(() => percentile(durationValues.value, 95))
  const passRate = computed(() =>
    aggregateStats.value.total
      ? Math.round((aggregateStats.value.passed / aggregateStats.value.total) * 100)
      : 0,
  )
  const incidentRate = computed(() => {
    const incidents = aggregateStats.value.failed + aggregateStats.value.broken
    return aggregateStats.value.total ? Math.round((incidents / aggregateStats.value.total) * 100) : 0
  })

  const historyByTest = computed(() => {
    const grouped = new Map<string, HistoryTestResult[]>()
    for (const result of historyResults.value) {
      const key = result.fullName || result.name || result.historyId || result.id
      if (!key) continue
      const bucket = grouped.get(key) ?? []
      bucket.push(result)
      grouped.set(key, bucket)
    }
    return grouped
  })

  const stabilitySummary = computed(() => {
    let flaky = 0
    let alwaysFailed = 0
    let alwaysPassed = 0
    for (const results of historyByTest.value.values()) {
      const statuses = new Set(results.map((result) => normalizeStatus(result.status)))
      const hasIncident = statuses.has('failed') || statuses.has('broken')
      const hasPassed = statuses.has('passed')
      if (hasIncident && hasPassed) flaky += 1
      if (hasIncident && !hasPassed) alwaysFailed += 1
      if (statuses.size === 1 && statuses.has('passed')) alwaysPassed += 1
    }
    return { uniqueTests: historyByTest.value.size, flaky, alwaysFailed, alwaysPassed }
  })

  const stabilityDetails = computed(() => {
    const flaky: StabilityDetailItem[] = []
    const alwaysFailed: StabilityDetailItem[] = []
    const alwaysPassed: StabilityDetailItem[] = []
    const incidents: StabilityDetailItem[] = []

    for (const [key, results] of historyByTest.value.entries()) {
      const statuses = new Set(results.map((result) => normalizeStatus(result.status)))
      const hasIncident = statuses.has('failed') || statuses.has('broken')
      const hasPassed = statuses.has('passed')
      const latest = [...results].sort((left, right) => (right.stop ?? 0) - (left.stop ?? 0))[0]
      const item = {
        key,
        name: latest?.fullName || latest?.name || key,
        lastStatus: normalizeStatus(latest?.status),
        incidents: results.filter((result) => {
          const status = normalizeStatus(result.status)
          return status === 'failed' || status === 'broken'
        }).length,
        totalRuns: results.length,
        history: [...results].sort((left, right) => (right.stop ?? 0) - (left.stop ?? 0)),
      }

      if (hasIncident) incidents.push(item)
      if (hasIncident && hasPassed) flaky.push(item)
      if (hasIncident && !hasPassed) alwaysFailed.push(item)
      if (statuses.size === 1 && statuses.has('passed')) alwaysPassed.push(item)
    }

    const sorter = (left: StabilityDetailItem, right: StabilityDetailItem) =>
      right.incidents - left.incidents || left.name.localeCompare(right.name)

    return {
      flaky: flaky.sort(sorter),
      alwaysFailed: alwaysFailed.sort(sorter),
      alwaysPassed: alwaysPassed.sort(sorter),
      incidents: incidents.sort(sorter),
    }
  })

  const stabilityDialog = computed(() => {
    if (!activeStabilityBucket.value) return null
    const titles: Record<StabilityBucketKey, string> = {
      flaky: 'Flaky tests',
      alwaysFailed: 'Always failed',
      alwaysPassed: 'Always passed',
      incidents: 'Incidents',
    }
    return {
      title: titles[activeStabilityBucket.value],
      items: stabilityDetails.value[activeStabilityBucket.value],
    }
  })

  const filteredStabilityDialogItems = computed(() => {
    if (!stabilityDialog.value) return []
    const query = stabilitySearch.value.trim().toLowerCase()
    if (!query) return stabilityDialog.value.items
    return stabilityDialog.value.items.filter((item) => item.name.toLowerCase().includes(query))
  })

  const selectedTestDetails = computed<SelectedTestDetails | null>(() => {
    if (!selectedTestKey.value) return null
    const history = historyByTest.value.get(selectedTestKey.value)
    if (!history?.length) return null
    const ordered = [...history].sort((left, right) => (right.stop ?? 0) - (left.stop ?? 0))
    const latest = ordered[0]
    const incidents = ordered.filter((result) => {
      const status = normalizeStatus(result.status)
      return status === 'failed' || status === 'broken'
    }).length
    return {
      name: latest?.fullName || latest?.name || selectedTestKey.value,
      lastStatus: normalizeStatus(latest?.status),
      totalRuns: ordered.length,
      incidents,
      history: ordered.slice(0, 8),
    }
  })

  watch(activeStabilityBucket, (value) => {
    if (!value) stabilitySearch.value = ''
  })

  watch(historyByTest, () => {
    if (selectedTestKey.value && !historyByTest.value.has(selectedTestKey.value)) {
      selectedTestKey.value = null
    }
  })

  const trendPoints = computed<HistoryPoint[]>(() =>
    [...filteredHistoryRuns.value]
      .sort((left, right) => left.timestamp - right.timestamp)
      .slice(-8)
      .map((run) => {
        const results = Object.values(run.testResults ?? {})
        let passed = 0
        let failed = 0
        let broken = 0
        for (const result of results) {
          const status = normalizeStatus(result.status)
          if (status === 'passed') passed += 1
          else if (status === 'failed') failed += 1
          else if (status === 'broken') broken += 1
        }
        const total = results.length
        return {
          key: run.uuid,
          label: buildRunLabel(run),
          total,
          passed,
          failed,
          broken,
          passRate: total ? Math.round((passed / total) * 100) : 0,
          reportId: reportMapByName.value.get(run.name) ?? null,
        }
      }),
  )

  const topUnstableTests = computed<UnstableTest[]>(() =>
    Array.from(historyByTest.value.entries())
      .map(([key, results]) => {
        const incidents = results.filter((result) => {
          const status = normalizeStatus(result.status)
          return status === 'failed' || status === 'broken'
        }).length
        const totalRuns = results.length
        const stability = totalRuns ? Math.round(((totalRuns - incidents) / totalRuns) * 100) : 0
        const latest = [...results].sort((left, right) => (right.stop ?? 0) - (left.stop ?? 0))[0]
        return {
          key,
          name: latest?.fullName || latest?.name || key,
          totalRuns,
          incidents,
          stability,
          lastStatus: normalizeStatus(latest?.status),
        }
      })
      .filter((item) => item.totalRuns > 1 && item.incidents > 0)
      .sort((left, right) =>
        left.stability - right.stability ||
        right.incidents - left.incidents ||
        right.totalRuns - left.totalRuns,
      )
      .slice(0, 6),
  )

  const failureSignatures = computed<FailureSignature[]>(() => {
    const counts = new Map<string, number>()
    for (const result of historyResults.value) {
      const status = normalizeStatus(result.status)
      if (status !== 'failed' && status !== 'broken') continue
      const signature = buildSignature(result)
      counts.set(signature, (counts.get(signature) ?? 0) + 1)
    }
    return Array.from(counts.entries())
      .map(([signature, count]) => ({ signature, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 5)
  })

  const tagHealth = computed<TagHealth[]>(() => {
    const counts = new Map<string, { total: number; incidents: number }>()
    for (const result of historyResults.value) {
      const tags = (result.labels ?? []).filter((label) => label.name === 'tag' && label.value).map((label) => label.value)
      const status = normalizeStatus(result.status)
      const hasIncident = status === 'failed' || status === 'broken'
      for (const tag of tags) {
        const bucket = counts.get(tag) ?? { total: 0, incidents: 0 }
        bucket.total += 1
        if (hasIncident) bucket.incidents += 1
        counts.set(tag, bucket)
      }
    }
    return Array.from(counts.entries())
      .map(([tag, value]) => ({
        tag,
        total: value.total,
        incidents: value.incidents,
        healthyRate: value.total ? Math.round(((value.total - value.incidents) / value.total) * 100) : 0,
      }))
      .sort((left, right) => right.incidents - left.incidents || left.healthyRate - right.healthyRate)
      .slice(0, 5)
  })

  const reportsWithStats = computed(() => props.reports.filter((report) => report.stats))

  const topProblemRuns = computed<ProblemRunItem[]>(() =>
    [...reportsWithStats.value]
      .map((report) => ({
        report,
        incidents: (report.stats?.failed ?? 0) + (report.stats?.broken ?? 0),
      }))
      .sort(
        (left, right) =>
          right.incidents - left.incidents ||
          toTimestamp(right.report.created_at) - toTimestamp(left.report.created_at),
      )
      .slice(0, 4),
  )

  const recentReports = computed<RecentReportItem[]>(() =>
    [...reportsWithStats.value]
      .sort((left, right) => toTimestamp(left.created_at) - toTimestamp(right.created_at))
      .slice(-4)
      .map((report) => {
        const total = report.stats?.total ?? 0
        const incidents = (report.stats?.failed ?? 0) + (report.stats?.broken ?? 0)
        return {
          id: report.id,
          label: props.getReportTitle(report) ?? report.id,
          healthy: total > 0 ? Math.max(0, Math.round(((total - incidents) / total) * 100)) : 0,
          incidents,
          total,
          selected: report.id === props.selectedReportId,
        }
      }),
  )

  const ringStyle = computed(() => {
    const safePassRate = Math.max(0, Math.min(100, passRate.value))
    return {
      background: `conic-gradient(#22c55e 0 ${safePassRate}%, #ef4444 ${safePassRate}% ${safePassRate + Math.min(100 - safePassRate, incidentRate.value)}%, rgba(148, 163, 184, 0.18) ${safePassRate + Math.min(100 - safePassRate, incidentRate.value)}% 100%)`,
    }
  })

  return {
    activeEnvironment,
    activeSignature,
    activeStabilityBucket,
    activeTags,
    activeSuite,
    aggregateStats,
    failureSignatures,
    filterOptions,
    filteredHistoryRuns,
    filteredStabilityDialogItems,
    incidentRate,
    normalizeStatus,
    openReport,
    p95Duration,
    passRate,
    recentReports,
    ringStyle,
    selectedTestDetails,
    stabilityDialog,
    stabilitySearch,
    stabilitySummary,
    tagHealth,
    toggleSignature,
    toggleTag,
    topProblemRuns,
    topUnstableTests,
    trendPoints,
    setActiveStabilityBucket: (bucket: StabilityBucketKey | null) => {
      activeStabilityBucket.value = bucket
    },
    setStabilitySearch: (value: string) => {
      stabilitySearch.value = value
    },
    selectTest: (key: string) => {
      selectedTestKey.value = key
      activeStabilityBucket.value = null
    },
    resetFilters: () => {
      activeTags.value = []
      activeSuite.value = 'all'
      activeEnvironment.value = 'all'
      activeSignature.value = 'all'
    },
  }
}
