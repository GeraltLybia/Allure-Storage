<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppHeader from '../../components/common/reports/AppHeader.vue'
import ReportsSidebar from '../../components/common/reports/ReportsSidebar.vue'
import ReportViewer from '../../components/common/reports/ReportViewer.vue'
import { useReports } from '../../composables/useReports'
import { useTheme } from '../../composables/useTheme'

const {
  downloadHistory,
  error,
  handleDeleteReport,
  handleDownloadReport,
  handleHistoryUpload,
  handleUploadReport,
  historyInfo,
  loading,
  loadReports,
  reports,
  reportsLoaded,
  setSidebarCollapsed,
  selectedReportId,
  sidebarCollapsed,
  sidebarVisible,
  uploading,
  viewerSrc,
} = useReports()

const { theme, toggleTheme } = useTheme()
const route = useRoute()
const router = useRouter()

const routeReportId = computed(() => {
  const value = route.params.reportId
  return typeof value === 'string' ? value : null
})

function openReport(id: string) {
  selectedReportId.value = id
  if (routeReportId.value !== id) {
    router.push({ name: 'report-by-id', params: { reportId: id } })
  }
}

watch(selectedReportId, (id) => {
  if (id && routeReportId.value !== id) {
    router.push({ name: 'report-by-id', params: { reportId: id } })
  }
})

watch(selectedReportId, (id) => {
  if (id && routeReportId.value !== id) {
    router.push({ name: 'report-by-id', params: { reportId: id } })
  }
})

watch(
  [reports, routeReportId, reportsLoaded],
  ([items, reportId, loaded]) => {
    if (!loaded) {
      return
    }

    if (items.length === 0) {
      selectedReportId.value = null
      if (reportId) {
        router.replace({ name: 'reports' })
      }
      return
    }

    if (reportId) {
      const exists = items.some((report) => report.id === reportId)
      if (exists) {
        selectedReportId.value = reportId
        return
      }

      selectedReportId.value = null
      router.replace({ name: 'reports' })
      return
    }

    if (!selectedReportId.value) {
      const firstReport = items[0]
      if (!firstReport) return
      const firstReportId = firstReport.id
      selectedReportId.value = firstReportId
      router.replace({ name: 'report-by-id', params: { reportId: firstReportId } })
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="reports-view">
    <AppHeader
      :sidebar-visible="sidebarVisible"
      :theme="theme"
      :uploading="uploading"
      @toggle-sidebar="sidebarVisible = !sidebarVisible"
      @toggle-theme="toggleTheme"
      @upload-report="handleUploadReport"
    />

    <div v-if="error" class="reports-view-error" role="alert">
      <p>{{ error }}</p>
      <button type="button" class="text-button" @click="loadReports()">Повторить</button>
    </div>

    <main
      class="reports-view-main"
      :class="{
        'reports-view-main--no-sidebar': !sidebarVisible,
        'reports-view-main--collapsed': sidebarVisible && sidebarCollapsed,
      }"
    >
      <ReportsSidebar
        v-if="sidebarVisible"
        :collapsed="sidebarCollapsed"
        :loading="loading"
        :reports="reports"
        :selected-report-id="selectedReportId"
        :history-info="historyInfo"
        @refresh="loadReports"
        @collapse="setSidebarCollapsed(true)"
        @expand="setSidebarCollapsed(false)"
        @select-report="openReport"
        @download-report="handleDownloadReport"
        @delete-report="handleDeleteReport"
        @download-history="downloadHistory"
        @upload-history="handleHistoryUpload"
      />

      <ReportViewer :sidebar-visible="sidebarVisible" :viewer-src="viewerSrc" @show-sidebar="sidebarVisible = true" />
    </main>
  </div>
</template>

<style scoped src="../../assets/style/views/reports/ReportsView.css"></style>
