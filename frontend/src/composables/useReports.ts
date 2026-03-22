import { computed, onMounted, ref } from 'vue'

import {
  deleteReport,
  fetchHistoryInfo,
  fetchHistoryRuns,
  fetchReports,
  uploadHistory,
  uploadReport,
} from '../api/reports'
import { formatDate, formatDuration, formatSize, getReportTitle } from '../utils/reports'
import type { HistoryInfo, HistoryRun, Report } from '../types/reports'

export function useReports(options?: { loadHistoryRunsOnMounted?: boolean }) {
  const reports = ref<Report[]>([])
  const selectedReportId = ref<string | null>(null)
  const loading = ref(false)
  const reportsLoaded = ref(false)
  const uploading = ref(false)
  const error = ref<string | null>(null)
  const historyInfo = ref<HistoryInfo | null>(null)
  const historyRuns = ref<HistoryRun[]>([])
  const historyLoading = ref(false)
  const sidebarVisible = ref(true)

  const selectedReport = computed(() => {
    if (!selectedReportId.value) return null
    return reports.value.find((report) => report.id === selectedReportId.value) ?? null
  })

  const viewerSrc = computed(() => {
    if (!selectedReport.value) return null
    if (selectedReport.value.entry_path) {
      return `/reports-static/${selectedReport.value.entry_path}`
    }
    return `/reports-static/${selectedReport.value.id}/index.html`
  })

  async function loadReports() {
    try {
      loading.value = true
      error.value = null
      const data = await fetchReports()
      reports.value = data
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
      // No-op for this side panel widget.
    }
  }

  async function loadHistoryRuns() {
    try {
      historyLoading.value = true
      historyRuns.value = await fetchHistoryRuns()
    } catch {
      historyRuns.value = []
    } finally {
      historyLoading.value = false
    }
  }

  async function handleUploadReport(event: Event) {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return

    uploading.value = true
    error.value = null
    try {
      await uploadReport(file)
      await loadReports()
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
        selectedReportId.value = null
      }
    } catch (exception) {
      error.value = (exception as Error).message
    }
  }

  function handleDownloadReport(id: string) {
    window.open(`/api/reports/${id}/download`, '_blank')
  }

  async function handleHistoryUpload(event: Event) {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return

    error.value = null
    try {
      await uploadHistory(file)
      await loadHistoryInfo()
      await loadHistoryRuns()
    } catch (exception) {
      error.value = (exception as Error).message
    } finally {
      input.value = ''
    }
  }

  function downloadHistory() {
    window.location.href = '/api/history'
  }

  onMounted(() => {
    loadReports()
    loadHistoryInfo()
    if (options?.loadHistoryRunsOnMounted ?? true) {
      loadHistoryRuns()
    }
  })

  return {
    downloadHistory,
    error,
    formatDate,
    formatDuration,
    formatSize,
    getReportTitle,
    handleDeleteReport,
    handleDownloadReport,
    handleHistoryUpload,
    handleUploadReport,
    historyLoading,
    historyInfo,
    historyRuns,
    loading,
    loadHistoryRuns,
    loadReports,
    reports,
    reportsLoaded,
    selectedReportId,
    sidebarVisible,
    uploading,
    viewerSrc,
  }
}
