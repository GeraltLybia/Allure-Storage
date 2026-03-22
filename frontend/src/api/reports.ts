import type {
  HistoryDashboardSummary,
  HistoryInfo,
  HistoryRun,
  HistorySelectedTestDetails,
  Report,
} from '../types/reports'

async function parseApiError(response: Response, fallback: string) {
  const payload = await response.json().catch(() => null)
  return payload?.detail ?? fallback
}

export async function fetchReports() {
  const response = await fetch('/api/reports')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки списка отчетов'))
  }
  return (await response.json()) as Report[]
}

export async function fetchHistoryInfo() {
  const response = await fetch('/api/history/info')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки history'))
  }
  return (await response.json()) as HistoryInfo
}

export async function fetchHistoryRuns() {
  const response = await fetch('/api/history')
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки history'))
  }

  const text = await response.text()
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as HistoryRun)
}

type HistoryDashboardFilters = {
  tags?: string[]
  suite?: string
  environment?: string
  signature?: string
}

function buildHistoryDashboardQuery(filters: HistoryDashboardFilters) {
  const query = new URLSearchParams()
  if (filters.tags?.length) query.set('tags', filters.tags.join(','))
  if (filters.suite && filters.suite !== 'all') query.set('suite', filters.suite)
  if (filters.environment && filters.environment !== 'all') query.set('environment', filters.environment)
  if (filters.signature && filters.signature !== 'all') query.set('signature', filters.signature)
  const value = query.toString()
  return value ? `?${value}` : ''
}

export async function fetchHistoryDashboard(filters: HistoryDashboardFilters) {
  const response = await fetch(`/api/history/dashboard${buildHistoryDashboardQuery(filters)}`)
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки dashboard history'))
  }
  return (await response.json()) as HistoryDashboardSummary
}

export async function fetchHistoryTestDetails(testKey: string, filters: HistoryDashboardFilters) {
  const response = await fetch(
    `/api/history/dashboard/tests/${encodeURIComponent(testKey)}${buildHistoryDashboardQuery(filters)}`,
  )
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки деталей теста'))
  }
  return (await response.json()) as HistorySelectedTestDetails
}

export async function uploadReport(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/reports/upload', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки отчета'))
  }
}

export async function deleteReport(reportId: string) {
  const response = await fetch(`/api/reports/${reportId}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка удаления отчета'))
  }
}

export async function uploadHistory(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/history', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки history'))
  }
}
