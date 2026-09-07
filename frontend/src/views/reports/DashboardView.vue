<script setup lang="ts">
import AppHeader from '../../components/common/reports/AppHeader.vue'
import ReportsDashboard from '../../components/common/reports/ReportsDashboard.vue'
import { useReports } from '../../composables/useReports'
import { useTheme } from '../../composables/useTheme'

const { handleUploadReport, reports, selectedReportId, uploading } = useReports()

const { theme, toggleTheme } = useTheme()
</script>

<template>
  <div class="dashboard-view">
    <AppHeader
      :sidebar-visible="false"
      :show-sidebar-toggle="false"
      :theme="theme"
      :uploading="uploading"
      @toggle-theme="toggleTheme"
      @upload-report="handleUploadReport"
    />

    <ReportsDashboard :reports="reports" :selected-report-id="selectedReportId" />
  </div>
</template>

<style scoped src="../../assets/style/views/reports/DashboardView.css"></style>
