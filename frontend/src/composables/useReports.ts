import { computed, onMounted, ref } from 'vue'

import {
  deleteReport,
  fetchHistoryInfo,
  fetchReports,
  historyDownloadUrl,
  reportDownloadUrl,
  reportStaticUrl,
  uploadHistory,
  uploadReport,
} from '../api/reports'
import type { HistoryInfo, Report } from '../types/reports'

const reports = ref<Report[]>([])
const selectedReportId = ref<string | null>(null)
const loading = ref(false)
const reportsLoaded = ref(false)
const uploading = ref(false)
const error = ref<string | null>(null)
const historyInfo = ref<HistoryInfo | null>(null)
const sidebarVisible = ref(true)
function readSidebarCollapsed() {
  try {
    return localStorage.getItem('allure-storage:reports-sidebar-collapsed') === '1'
  } catch {
    return false
  }
}

const sidebarCollapsed = ref(readSidebarCollapsed())

function setSidebarCollapsed(value: boolean) {
  sidebarCollapsed.value = value
  try {
    localStorage.setItem('allure-storage:reports-sidebar-collapsed', value ? '1' : '0')
  } catch {
    // localStorage может быть недоступен
  }
}

const selectedReport = computed(() => {
  if (!selectedReportId.value) return null
  return reports.value.find((report) => report.id === selectedReportId.value) ?? null
})

const viewerSrc = computed(() => {
  const report = selectedReport.value
  if (!report) return null
  return reportStaticUrl(report)
})

async function loadReports() {
  if (loading.value) return
  loading.value = true
  error.value = null
  try {
    reports.value = await fetchReports()
  } catch (exception) {
    error.value = (exception as Error).message
  } finally {
    loading.value = false
    reportsLoaded.value = true
  }
}

async function loadHistoryInfo() {
  try {
    historyInfo.value = await fetchHistoryInfo()
  } catch {
    // Side-panel widget; ignore when unavailable.
  }
}

function ensureLoaded() {
  if (!reportsLoaded.value && !loading.value) {
    void loadReports()
    void loadHistoryInfo()
  }
}

async function handleUploadReport(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || uploading.value) return

  uploading.value = true
  error.value = null
  try {
    const result = await uploadReport(file)
    const existingIndex = reports.value.findIndex((item) => item.id === result.report.id)
    if (existingIndex >= 0) {
      reports.value.splice(existingIndex, 1, result.report)
    } else {
      reports.value.unshift(result.report)
    }
    selectedReportId.value = result.report.id
    void loadHistoryInfo()
  } catch (exception) {
    error.value = (exception as Error).message
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function handleDeleteReport(id: string) {
  if (!window.confirm('Удалить отчет?')) return

  error.value = null
  try {
    await deleteReport(id)
    reports.value = reports.value.filter((report) => report.id !== id)
    if (selectedReportId.value === id) {
      selectedReportId.value = reports.value[0]?.id ?? null
    }
  } catch (exception) {
    error.value = (exception as Error).message
  }
}

function handleDownloadReport(id: string) {
  window.open(reportDownloadUrl(id), '_blank')
}

async function handleHistoryUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  error.value = null
  try {
    await uploadHistory(file)
    await loadHistoryInfo()
  } catch (exception) {
    error.value = (exception as Error).message
  } finally {
    input.value = ''
  }
}

function downloadHistory() {
  window.location.href = historyDownloadUrl()
}

export function useReports() {
  onMounted(ensureLoaded)

  return {
    downloadHistory,
    error,
    handleDeleteReport,
    handleDownloadReport,
    handleHistoryUpload,
    handleUploadReport,
    historyInfo,
    loadReports,
    loading,
    reports,
    reportsLoaded,
    selectedReport,
    selectedReportId,
    setSidebarCollapsed,
    sidebarCollapsed,
    sidebarVisible,
    uploading,
    viewerSrc,
  }
}
