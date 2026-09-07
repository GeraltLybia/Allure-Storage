import type { HistoryDashboardSummary, HistoryInfo, HistorySelectedTestDetails, Report } from '../types/reports'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '') as string

function apiUrl(path: string) {
  return `${API_BASE}${path}`
}

type ApiErrorDetail = string | Array<{ loc?: unknown; msg?: unknown; type?: unknown }> | null | undefined

async function parseApiError(response: Response, fallback: string) {
  const payload = (await response.json().catch(() => null)) as { detail?: ApiErrorDetail } | null
  const detail = payload?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === 'object' ? item.msg : null))
      .filter((msg): msg is string => typeof msg === 'string' && msg.trim().length > 0)
    if (messages.length) return messages.join('; ')
  }
  return fallback
}

export async function fetchReports() {
  const response = await fetch(apiUrl('/api/reports'))
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки списка отчетов'))
  }
  return (await response.json()) as Report[]
}

export async function fetchHistoryInfo() {
  const response = await fetch(apiUrl('/api/history/info'))
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки history'))
  }
  return (await response.json()) as HistoryInfo
}

type HistoryDashboardFilters = {
  tags?: string[]
  suite?: string
  environment?: string
  signature?: string
  stopFrom?: number
  stopTo?: number
}

function buildHistoryDashboardQuery(filters: HistoryDashboardFilters) {
  const query = new URLSearchParams()
  if (filters.tags?.length) query.set('tags', filters.tags.join(','))
  if (filters.suite && filters.suite !== 'all') query.set('suite', filters.suite)
  if (filters.environment && filters.environment !== 'all') query.set('environment', filters.environment)
  if (filters.signature && filters.signature !== 'all') query.set('signature', filters.signature)
  if (typeof filters.stopFrom === 'number' && Number.isFinite(filters.stopFrom)) {
    query.set('stopFrom', String(filters.stopFrom))
  }
  if (typeof filters.stopTo === 'number' && Number.isFinite(filters.stopTo)) {
    query.set('stopTo', String(filters.stopTo))
  }
  const value = query.toString()
  return value ? `?${value}` : ''
}

export async function fetchHistoryDashboard(filters: HistoryDashboardFilters) {
  const response = await fetch(apiUrl(`/api/history/dashboard${buildHistoryDashboardQuery(filters)}`))
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки dashboard history'))
  }
  return (await response.json()) as HistoryDashboardSummary
}

export async function fetchHistoryTestDetails(testKey: string, filters: HistoryDashboardFilters) {
  const response = await fetch(
    apiUrl(`/api/history/dashboard/tests/${encodeURIComponent(testKey)}${buildHistoryDashboardQuery(filters)}`),
  )
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки деталей теста'))
  }
  return (await response.json()) as HistorySelectedTestDetails
}

export type UploadResult = {
  id: string
  message: string
  report: Report
}

export async function uploadReport(file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(apiUrl('/api/reports/upload'), {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки отчета'))
  }
  return (await response.json()) as UploadResult
}

export async function deleteReport(reportId: string) {
  const response = await fetch(apiUrl(`/api/reports/${encodeURIComponent(reportId)}`), { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка удаления отчета'))
  }
}

export async function uploadHistory(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(apiUrl('/api/history'), {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Ошибка загрузки history'))
  }
}

export function reportDownloadUrl(reportId: string) {
  return apiUrl(`/api/reports/${encodeURIComponent(reportId)}/download`)
}

export function reportStaticUrl(report: Report) {
  if (report.entry_path) {
    const segments = report.entry_path.split('/').map(encodeURIComponent)
    return apiUrl(`/reports-static/${segments.join('/')}`)
  }
  return apiUrl(`/reports-static/${encodeURIComponent(report.id)}/index.html`)
}

export function historyDownloadUrl() {
  return apiUrl('/api/history')
}
