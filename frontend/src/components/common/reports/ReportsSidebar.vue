<script setup lang="ts">
import ReportListItem from './ReportListItem.vue'
import { formatDate, getPassRate, getRingStyle, getRingTitle } from '../../../utils/reports'

import type { HistoryInfo, Report } from '../../../types/reports'

defineProps<{
  collapsed: boolean
  loading: boolean
  reports: Report[]
  selectedReportId: string | null
  historyInfo: HistoryInfo | null
}>()

const emit = defineEmits<{
  collapse: []
  expand: []
  refresh: []
  selectReport: [id: string]
  downloadReport: [id: string]
  deleteReport: [id: string]
  downloadHistory: []
  uploadHistory: [event: Event]
}>()
</script>

<template>
  <section class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <button
      v-if="collapsed"
      class="sidebar-toggle"
      type="button"
      title="Развернуть список отчётов"
      aria-label="Развернуть список отчётов"
      @click="emit('expand')"
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
        <path d="m18 6-6 6 6 6" />
        <path d="m11 6-6 6 6 6" />
      </svg>
    </button>
    <div class="sidebar-header">
      <div class="sidebar-title">
        <span>Отчеты</span>
        <span v-if="loading" class="chip">Загрузка…</span>
      </div>
      <div class="sidebar-header-actions">
        <button class="text-button" type="button" @click="emit('refresh')">Обновить</button>
        <button
          v-if="!collapsed"
          class="icon-button"
          type="button"
          title="Свернуть список отчётов"
          aria-label="Свернуть список отчётов"
          @click="emit('collapse')"
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
            <path d="m6 6 6 6-6 6" />
            <path d="m13 6 6 6-6 6" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="!reports.length && !loading" class="empty-state">
      <p>Пока нет ни одного отчета.</p>
      <p>Загрузите ZIP c Allure отчетом, чтобы начать.</p>
    </div>

    <div class="sidebar-content">
      <ul class="report-list">
        <ReportListItem
          v-for="report in reports"
          :key="report.id"
          :report="report"
          :active="report.id === selectedReportId"
          @select="emit('selectReport', $event)"
          @download="emit('downloadReport', $event)"
          @delete="emit('deleteReport', $event)"
        />
      </ul>
      <ul class="report-rail">
        <li
          v-for="report in reports"
          :key="`rail-${report.id}`"
          class="report-rail-item"
          :class="{ 'report-rail-item--active': report.id === selectedReportId }"
          role="button"
          tabindex="0"
          :title="getRingTitle(report)"
          @click="emit('selectReport', report.id)"
          @keydown.enter.prevent="emit('selectReport', report.id)"
          @keydown.space.prevent="emit('selectReport', report.id)"
        >
          <div class="report-ring" :style="getRingStyle(report)">
            <span v-if="report.stats">{{ getPassRate(report) }}%</span>
          </div>
        </li>
      </ul>
    </div>

    <div class="history-card">
      <div class="history-header">
        <span>История</span>
        <span v-if="historyInfo" class="history-meta">
          {{ historyInfo.records }} записей ·
          {{ historyInfo.updated_at ? formatDate(historyInfo.updated_at) : 'нет данных' }}
        </span>
      </div>
      <div class="history-actions">
        <button type="button" class="text-button" @click="emit('downloadHistory')">Скачать history.jsonl</button>
        <label class="text-button">
          Загрузить history.jsonl
          <input type="file" accept=".json,.jsonl" @change="emit('uploadHistory', $event)" />
        </label>
      </div>
    </div>
  </section>
</template>

<style scoped src="../../../assets/style/components/reports/ReportsSidebar.css"></style>
