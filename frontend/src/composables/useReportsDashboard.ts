import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchHistoryDashboard, fetchHistoryTestDetails } from '../api/reports'
import type {
  HistoryDashboardSummary,
  HistorySelectedTestDetails,
  Report,
} from '../types/reports'
import type {
  ProblemRunItem,
  RecentReportItem,
  StabilityBucketKey,
} from '../components/common/reports/dashboard/types'

export function useReportsDashboard(props: {
  reports: Report[]
  selectedReportId: string | null
  getReportTitle: (report: Report) => string | undefined
}) {
  const route = useRoute()
  const router = useRouter()

  const activeTags = ref<string[]>([])
  const activeSuite = ref('all')
  const activeEnvironment = ref('all')
  const activeSignature = ref('all')
  const activeDateFrom = ref('')
  const activeDateTo = ref('')
  const activeStabilityBucket = ref<StabilityBucketKey | null>(null)
  const stabilitySearch = ref('')
  const selectedTestKey = ref<string | null>(null)
  const dashboardData = ref<HistoryDashboardSummary | null>(null)
  const selectedTestDetails = ref<HistorySelectedTestDetails | null>(null)
  const loading = ref(false)

  function parseQueryList(value: unknown) {
    if (typeof value !== 'string') return []
    return value.split(',').map((item) => item.trim()).filter(Boolean)
  }

  function isValidDateInput(value: string) {
    return /^\d{4}-\d{2}-\d{2}$/.test(value)
  }

  function dateStartTimestamp(value: string) {
    if (!isValidDateInput(value)) return undefined
    const [year = 0, month = 1, day = 1] = value.split('-').map(Number)
    const timestamp = new Date(year, month - 1, day, 0, 0, 0, 0).getTime()
    return Number.isFinite(timestamp) ? timestamp : undefined
  }

  function dateEndTimestamp(value: string) {
    if (!isValidDateInput(value)) return undefined
    const [year = 0, month = 1, day = 1] = value.split('-').map(Number)
    const timestamp = new Date(year, month - 1, day, 23, 59, 59, 999).getTime()
    return Number.isFinite(timestamp) ? timestamp : undefined
  }

  function arraysEqual(left: string[], right: string[]) {
    if (left.length !== right.length) return false
    return left.every((item, index) => item === right[index])
  }

  function normalizeStatus(value: string | undefined) {
    return value?.trim().toLowerCase() ?? 'unknown'
  }

  function currentFilters() {
    const stopFrom = dateStartTimestamp(activeDateFrom.value)
    const stopTo = dateEndTimestamp(activeDateTo.value)

    return {
      tags: activeTags.value,
      suite: activeSuite.value,
      environment: activeEnvironment.value,
      signature: activeSignature.value,
      stopFrom,
      stopTo,
    }
  }

  async function loadDashboard() {
    try {
      loading.value = true
      dashboardData.value = await fetchHistoryDashboard(currentFilters())
    } catch {
      dashboardData.value = null
    } finally {
      loading.value = false
    }
  }

  async function loadSelectedTestDetails() {
    if (!selectedTestKey.value) {
      selectedTestDetails.value = null
      return
    }

    try {
      selectedTestDetails.value = await fetchHistoryTestDetails(selectedTestKey.value, currentFilters())
    } catch {
      selectedTestDetails.value = null
    }
  }

  function toggleTag(tag: string) {
    activeTags.value = activeTags.value.includes(tag)
      ? activeTags.value.filter((item) => item !== tag)
      : [...activeTags.value, tag].sort((left, right) => left.localeCompare(right))
  }

  function toggleSignature(signature: string) {
    activeSignature.value = activeSignature.value === signature ? 'all' : signature
  }

  function openReport(id: string) {
    router.push({ name: 'report-by-id', params: { reportId: id } })
  }

  watch(
    () => route.query,
    (query) => {
      const nextTags = parseQueryList(query.tags).sort((left, right) => left.localeCompare(right))
      const nextSuite = typeof query.suite === 'string' ? query.suite : 'all'
      const nextEnvironment = typeof query.environment === 'string' ? query.environment : 'all'
      const nextSignature = typeof query.signature === 'string' ? query.signature : 'all'
      const nextDateFrom = typeof query.dateFrom === 'string' && isValidDateInput(query.dateFrom) ? query.dateFrom : ''
      const nextDateTo = typeof query.dateTo === 'string' && isValidDateInput(query.dateTo) ? query.dateTo : ''

      if (!arraysEqual(activeTags.value, nextTags)) activeTags.value = nextTags
      activeSuite.value = nextSuite
      activeEnvironment.value = nextEnvironment
      activeSignature.value = nextSignature
      activeDateFrom.value = nextDateFrom
      activeDateTo.value = nextDateTo
    },
    { immediate: true },
  )

  watch(activeDateFrom, (value) => {
    if (activeDateTo.value && value && activeDateTo.value < value) {
      activeDateTo.value = value
    }
  })

  watch(activeDateTo, (value) => {
    if (activeDateFrom.value && value && value < activeDateFrom.value) {
      activeDateFrom.value = value
    }
  })

  watch([activeTags, activeSuite, activeEnvironment, activeSignature, activeDateFrom, activeDateTo], async () => {
    const nextQuery: Record<string, string> = {}
    if (activeTags.value.length) nextQuery.tags = activeTags.value.join(',')
    if (activeSuite.value !== 'all') nextQuery.suite = activeSuite.value
    if (activeEnvironment.value !== 'all') nextQuery.environment = activeEnvironment.value
    if (activeSignature.value !== 'all') nextQuery.signature = activeSignature.value
    if (isValidDateInput(activeDateFrom.value)) nextQuery.dateFrom = activeDateFrom.value
    if (isValidDateInput(activeDateTo.value)) nextQuery.dateTo = activeDateTo.value

    const currentTags = parseQueryList(route.query.tags).sort((left, right) => left.localeCompare(right))
    const currentSuite = typeof route.query.suite === 'string' ? route.query.suite : 'all'
    const currentEnvironment = typeof route.query.environment === 'string' ? route.query.environment : 'all'
    const currentSignature = typeof route.query.signature === 'string' ? route.query.signature : 'all'
    const currentDateFrom =
      typeof route.query.dateFrom === 'string' && isValidDateInput(route.query.dateFrom)
        ? route.query.dateFrom
        : ''
    const currentDateTo =
      typeof route.query.dateTo === 'string' && isValidDateInput(route.query.dateTo)
        ? route.query.dateTo
        : ''

    if (
      !(
        arraysEqual(currentTags, activeTags.value) &&
        currentSuite === activeSuite.value &&
        currentEnvironment === activeEnvironment.value &&
        currentSignature === activeSignature.value &&
        currentDateFrom === activeDateFrom.value &&
        currentDateTo === activeDateTo.value
      )
    ) {
      await router.replace({ query: nextQuery })
    }

    await loadDashboard()
    await loadSelectedTestDetails()
  }, { immediate: true })

  watch(activeStabilityBucket, (value) => {
    if (!value) stabilitySearch.value = ''
  })

  const filterOptions = computed(
    () => dashboardData.value?.filterOptions ?? { tags: [], suites: [], environments: [] },
  )
  const dateToMin = computed(() => activeDateFrom.value || undefined)
  const dateFromMax = computed(() => activeDateTo.value || undefined)
  const filteredRunCount = computed(() => dashboardData.value?.filteredRunCount ?? 0)
  const aggregateStats = computed(
    () =>
      dashboardData.value?.aggregateStats ?? {
        total: 0,
        passed: 0,
        failed: 0,
        broken: 0,
        flaky: 0,
        other: 0,
      },
  )
  const p95Duration = computed(() => dashboardData.value?.p95Duration ?? null)
  const passRate = computed(() => dashboardData.value?.passRate ?? 0)
  const incidentRate = computed(() => dashboardData.value?.incidentRate ?? 0)
  const stabilitySummary = computed(
    () =>
      dashboardData.value?.stabilitySummary ?? {
        uniqueTests: 0,
        flaky: 0,
        alwaysFailed: 0,
        alwaysPassed: 0,
      },
  )
  const failureSignatures = computed(() => dashboardData.value?.failureSignatures ?? [])
  const tagHealth = computed(() => dashboardData.value?.tagHealth ?? [])
  const trendPoints = computed(() => {
    const reportMapByName = new Map<string, string>()
    for (const report of props.reports) {
      const keys = [report.name, props.getReportTitle(report)].filter(
        (value): value is string => Boolean(value?.trim()),
      )
      for (const key of keys) reportMapByName.set(key, report.id)
    }

    return (dashboardData.value?.trendPoints ?? []).map((item) => ({
      ...item,
      reportId: item.reportName ? reportMapByName.get(item.reportName) ?? null : null,
    }))
  })
  const topUnstableTests = computed(() => dashboardData.value?.topUnstableTests ?? [])

  const stabilityDialog = computed(() => {
    if (!activeStabilityBucket.value) return null
    const titles: Record<StabilityBucketKey, string> = {
      flaky: 'Flaky tests',
      alwaysFailed: 'Always failed',
      alwaysPassed: 'Always passed',
      incidents: 'Incidents',
    }
    const items = dashboardData.value?.stabilityDetails?.[activeStabilityBucket.value] ?? []
    return {
      title: titles[activeStabilityBucket.value],
      items,
    }
  })

  const filteredStabilityDialogItems = computed(() => {
    if (!stabilityDialog.value) return []
    const query = stabilitySearch.value.trim().toLowerCase()
    if (!query) return stabilityDialog.value.items
    return stabilityDialog.value.items.filter((item) => item.name.toLowerCase().includes(query))
  })

  function toTimestamp(value: string) {
    const timestamp = new Date(value).getTime()
    return Number.isFinite(timestamp) ? timestamp : 0
  }

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
    activeDateFrom,
    activeDateTo,
    activeSignature,
    activeStabilityBucket,
    activeTags,
    activeSuite,
    aggregateStats,
    dateFromMax,
    dateToMin,
    failureSignatures,
    filterOptions,
    filteredRunCount,
    filteredStabilityDialogItems,
    historyLoading: loading,
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
    selectTest: async (key: string) => {
      selectedTestKey.value = key
      activeStabilityBucket.value = null
      await loadSelectedTestDetails()
    },
    resetFilters: () => {
      activeTags.value = []
      activeSuite.value = 'all'
      activeEnvironment.value = 'all'
      activeSignature.value = 'all'
      activeDateFrom.value = ''
      activeDateTo.value = ''
    },
  }
}
