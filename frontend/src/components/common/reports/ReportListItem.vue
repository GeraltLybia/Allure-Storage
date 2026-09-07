<script setup lang="ts">
import { formatDate, formatDuration, formatSize, getReportTitle } from '../../../utils/reports'
import type { Report } from '../../../types/reports'

const props = defineProps<{
  report: Report
  active: boolean
}>()

const emit = defineEmits<{
  select: [id: string]
  download: [id: string]
  delete: [id: string]
}>()

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    emit('select', props.report.id)
  }
}
</script>

<template>
  <li
    class="report-item"
    :class="{ 'report-item--active': active }"
    role="button"
    tabindex="0"
    :aria-label="`Открыть отчёт ${getReportTitle(report)}`"
    @click="emit('select', report.id)"
    @keydown="handleKeydown"
  >
    <div class="report-main">
      <div class="report-name" :title="getReportTitle(report)">
        {{ getReportTitle(report) }}
      </div>
      <div class="report-meta">
        <span>{{ formatDate(report.created_at) }}</span>
        <span>·</span>
        <span>{{ formatSize(report.size) }}</span>
        <span>·</span>
        <span>Длительность: {{ formatDuration(report.duration) }}</span>
        <span>·</span>
        <span class="report-id-short">{{ report.id.slice(0, 8) }}…</span>
      </div>
      <div v-if="report.status" class="report-status">
        <span class="stat-chip" :class="`status-chip status-chip--${report.status.toLowerCase()}`">
          Статус: {{ report.status }}
        </span>
      </div>
      <div v-if="report.stats" class="report-stats">
        <span class="stat-chip stat-chip--failed"> Сбоя: {{ report.stats.failed }} </span>
        <span class="stat-chip stat-chip--passed"> Пройдено: {{ report.stats.passed }} </span>
        <span class="stat-chip stat-chip--flaky"> Нестабильно: {{ report.stats.flaky }} </span>
        <span class="stat-chip stat-chip--broken"> Сломано: {{ report.stats.broken }} </span>
        <span class="stat-chip"> Всего: {{ report.stats.total }} </span>
      </div>
    </div>
    <div class="report-actions">
      <button
        type="button"
        class="icon-button"
        title="Скачать ZIP"
        aria-label="Скачать ZIP"
        @click.stop="emit('download', report.id)"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M12 3v12" />
          <path d="m7 11 5 5 5-5" />
          <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        </svg>
      </button>
      <button
        type="button"
        class="icon-button icon-button--danger"
        title="Удалить"
        aria-label="Удалить отчёт"
        @click.stop="emit('delete', report.id)"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M4 7h16" />
          <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
          <path d="m6 7 1 13a1 1 0 0 0 1 .9h8a1 1 0 0 0 1-.9L18 7" />
        </svg>
      </button>
    </div>
  </li>
</template>

<style scoped src="../../../assets/style/components/reports/ReportListItem.css"></style>
