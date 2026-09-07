import type { Report } from '../types/reports'

const DATE_LOCALE = 'ru-RU'

export function formatDate(value: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString(DATE_LOCALE, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatSize(bytes: number) {
  if (!bytes) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unit = 0

  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }

  return `${size.toFixed(1)} ${units[unit]}`
}

export function formatDuration(milliseconds: number | null | undefined) {
  if (milliseconds === null || milliseconds === undefined || Number.isNaN(milliseconds)) {
    return '-'
  }

  const safeValue = Math.max(0, Math.floor(milliseconds / 1000))
  const hours = Math.floor(safeValue / 3600)
  const minutes = Math.floor((safeValue % 3600) / 60)
  const secs = safeValue % 60

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

export function getReportTitle(report: Report) {
  if (report.name) {
    return report.name
  }

  const entryName = report.entry_path?.split('/').pop()
  if (entryName) {
    return entryName
  }

  return report.id
}

export function getPassRate(report: Report) {
  const s = report.stats
  return s && s.total ? Math.round((s.passed / s.total) * 100) : 0
}

export function getRingStyle(report: Report) {
  const s = report.stats
  const percent = (value: number) => (s && s.total ? (value / s.total) * 100 : 0)

  return {
    '--ring-passed': percent(s?.passed ?? 0),
    '--ring-flaky': percent(s?.flaky ?? 0),
    '--ring-broken': percent(s?.broken ?? 0),
    '--ring-failed': percent(s?.failed ?? 0),
  }
}

export function getRingTitle(report: Report) {
  const s = report.stats
  const base = getReportTitle(report)
  if (!s) return base
  return `${base} — пройдено: ${s.passed} · сбоя: ${s.failed} · нестабильно: ${s.flaky} · сломано: ${s.broken} · всего: ${s.total}`
}
