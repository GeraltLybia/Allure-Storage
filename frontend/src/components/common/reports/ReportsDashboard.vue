<script setup lang="ts">
import { reactive } from 'vue'

import DashboardFailureSignaturesPanel from './dashboard/DashboardFailureSignaturesPanel.vue'
import DashboardHealthPanel from './dashboard/DashboardHealthPanel.vue'
import DashboardProblemRunsPanel from './dashboard/DashboardProblemRunsPanel.vue'
import DashboardRecentReportsPanel from './dashboard/DashboardRecentReportsPanel.vue'
import DashboardStabilityModal from './dashboard/DashboardStabilityModal.vue'
import DashboardStabilityPanel from './dashboard/DashboardStabilityPanel.vue'
import DashboardTagHealthPanel from './dashboard/DashboardTagHealthPanel.vue'
import DashboardTestDetailsPanel from './dashboard/DashboardTestDetailsPanel.vue'
import DashboardTrendPanel from './dashboard/DashboardTrendPanel.vue'
import DashboardUnstablePanel from './dashboard/DashboardUnstablePanel.vue'
import { useReportsDashboard } from '../../../composables/useReportsDashboard'
import type { HistoryRun, Report } from '../../../types/reports'

const props = defineProps<{
  reports: Report[]
  historyRuns: HistoryRun[]
  historyLoading: boolean
  selectedReportId: string | null
  formatDuration: (value: number | null | undefined) => string
  getReportTitle: (report: Report) => string | undefined
}>()

const dashboard = reactive(useReportsDashboard(props))
</script>

<template>
  <section class="dashboard" aria-label="Dashboard">
    <div class="dashboard-hero">
      <div class="dashboard-copy">
        <span class="dashboard-eyebrow">Auto QA Observatory</span>
        <h2>История прогонов, стабильность и качество</h2>
        <p>
          Метрики строятся по `history.jsonl`: история тестов, нестабильность, сигнатуры падений
          и качество по тегам.
        </p>
      </div>

      <div class="dashboard-metrics">
        <article class="metric-card">
          <span class="metric-label">Runs</span>
          <strong class="metric-value">{{ dashboard.filteredHistoryRuns.length }}</strong>
          <span class="metric-note">прогонов после фильтрации</span>
        </article>
        <article class="metric-card">
          <span class="metric-label">Unique tests</span>
          <strong class="metric-value">{{ dashboard.stabilitySummary.uniqueTests }}</strong>
          <span class="metric-note">историй тест-кейсов</span>
        </article>
        <article class="metric-card metric-card--accent">
          <span class="metric-label">Pass rate</span>
          <strong class="metric-value">{{ dashboard.passRate }}%</strong>
          <span class="metric-note">по всем историческим результатам</span>
        </article>
        <article class="metric-card">
          <span class="metric-label">P95 duration</span>
          <strong class="metric-value">{{ formatDuration(dashboard.p95Duration) }}</strong>
          <span class="metric-note">длинный хвост времени выполнения</span>
        </article>
      </div>

      <div class="dashboard-filters">
        <div class="filters-heading">
          <span class="panel-kicker">Scope</span>
          <p>Фильтры ниже влияют на все метрики и виджеты на странице.</p>
        </div>

        <div class="filter-field filter-field--tags">
          <span>Tags</span>
          <div class="tag-filter-list">
            <button
              type="button"
              class="tag-filter-chip"
              :class="{ 'tag-filter-chip--active': dashboard.activeTags.length === 0 }"
              @click="dashboard.activeTags = []"
            >
              Все теги
            </button>
            <button
              v-for="tag in dashboard.filterOptions.tags"
              :key="tag"
              type="button"
              class="tag-filter-chip"
              :class="{ 'tag-filter-chip--active': dashboard.activeTags.includes(tag) }"
              @click="dashboard.toggleTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>

        <label class="filter-field">
          <span>Suite</span>
          <select v-model="dashboard.activeSuite">
            <option value="all">Все suite</option>
            <option v-for="suite in dashboard.filterOptions.suites" :key="suite" :value="suite">
              {{ suite }}
            </option>
          </select>
        </label>

        <label class="filter-field">
          <span>Environment</span>
          <select v-model="dashboard.activeEnvironment">
            <option value="all">Все environment</option>
            <option
              v-for="environment in dashboard.filterOptions.environments"
              :key="environment"
              :value="environment"
            >
              {{ environment }}
            </option>
          </select>
        </label>

        <label class="filter-field">
          <span>Failure signature</span>
          <select v-model="dashboard.activeSignature">
            <option value="all">Все сигнатуры</option>
            <option v-for="item in dashboard.failureSignatures" :key="item.signature" :value="item.signature">
              {{ item.signature }}
            </option>
          </select>
        </label>

        <button
          v-if="dashboard.activeTags.length || dashboard.activeSuite !== 'all' || dashboard.activeEnvironment !== 'all' || dashboard.activeSignature !== 'all'"
          type="button"
          class="filter-reset"
          @click="dashboard.resetFilters()"
        >
          Сбросить
        </button>
      </div>
    </div>

    <div v-if="historyLoading" class="dashboard-loading">
      Загрузка history.jsonl…
    </div>

    <div v-else-if="!dashboard.filteredHistoryRuns.length" class="dashboard-empty">
      <p>История прогонов пока не загружена.</p>
      <p>С текущими фильтрами данных нет. Сбрось фильтры или загрузи `history.jsonl`.</p>
    </div>

    <div v-else class="dashboard-grid">
      <DashboardHealthPanel
        :aggregate-stats="dashboard.aggregateStats"
        :incident-rate="dashboard.incidentRate"
        :pass-rate="dashboard.passRate"
        :ring-style="dashboard.ringStyle"
      />

      <DashboardStabilityPanel
        :aggregate-incidents="dashboard.aggregateStats.failed + dashboard.aggregateStats.broken"
        :stability-summary="dashboard.stabilitySummary"
        @open-bucket="dashboard.setActiveStabilityBucket($event)"
      />

      <DashboardTrendPanel
        :trend-points="dashboard.trendPoints"
        @open-report="dashboard.openReport($event)"
      />

      <DashboardUnstablePanel :top-unstable-tests="dashboard.topUnstableTests" />

      <DashboardTestDetailsPanel
        v-if="dashboard.selectedTestDetails"
        :selected-test-details="dashboard.selectedTestDetails"
        :format-duration="formatDuration"
        :normalize-status="dashboard.normalizeStatus"
      />

      <DashboardFailureSignaturesPanel
        :active-signature="dashboard.activeSignature"
        :failure-signatures="dashboard.failureSignatures"
        @toggle-signature="dashboard.toggleSignature($event)"
      />

      <DashboardTagHealthPanel
        :active-tags="dashboard.activeTags"
        :tag-health="dashboard.tagHealth"
        @toggle-tag="dashboard.toggleTag($event)"
      />

      <DashboardRecentReportsPanel
        :recent-reports="dashboard.recentReports"
        @open-report="dashboard.openReport($event)"
      />

      <DashboardProblemRunsPanel
        :get-report-title="getReportTitle"
        :selected-report-id="selectedReportId"
        :top-problem-runs="dashboard.topProblemRuns"
        @open-report="dashboard.openReport($event)"
      />
    </div>

    <DashboardStabilityModal
      v-if="dashboard.stabilityDialog"
      :items="dashboard.filteredStabilityDialogItems"
      :search="dashboard.stabilitySearch"
      :title="dashboard.stabilityDialog.title"
      @close="dashboard.setActiveStabilityBucket(null)"
      @select-test="dashboard.selectTest($event)"
      @update-search="dashboard.setStabilitySearch($event)"
    />
  </section>
</template>

<style src="../../../assets/style/components/reports/ReportsDashboard.css"></style>
