<script setup lang="ts">
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
import { formatDuration } from '../../../utils/reports'
import type { Report } from '../../../types/reports'

const props = defineProps<{
  reports: Report[]
  selectedReportId: string | null
}>()

const {
  activeDateFrom,
  activeDateTo,
  activeEnvironment,
  activeSignature,
  activeTags,
  activeSuite,
  aggregateStats,
  dashboardError,
  dateFromMax,
  dateToMin,
  failureSignatures,
  filterOptions,
  filteredRunCount,
  filteredStabilityDialogItems,
  historyLoading,
  incidentRate,
  normalizeStatus,
  openReport,
  p95Duration,
  passRate,
  recentReports,
  resetFilters,
  retryDashboard,
  ringStyle,
  selectTest,
  selectedTestDetails,
  setActiveStabilityBucket,
  setStabilitySearch,
  stabilityDialog,
  stabilitySearch,
  stabilitySummary,
  tagHealth,
  toggleSignature,
  toggleTag,
  topProblemRuns,
  topUnstableTests,
  trendPoints,
} = useReportsDashboard(props)
</script>

<template>
  <section class="dashboard" aria-label="Dashboard">
    <header class="dashboard-head">
      <div class="dashboard-copy">
        <span class="dashboard-eyebrow">Auto QA Observatory</span>
        <h2>История прогонов, стабильность и качество</h2>
        <p>
          Метрики строятся по `history.jsonl`: история тестов, нестабильность, сигнатуры падений и качество по тегам.
        </p>
      </div>

      <div class="dashboard-metrics">
        <article class="metric-card">
          <span class="metric-label">Прогонов</span>
          <strong class="metric-value">{{ filteredRunCount }}</strong>
          <span class="metric-note">прогонов после фильтрации</span>
        </article>
        <article class="metric-card">
          <span class="metric-label">Уникальных тестов</span>
          <strong class="metric-value">{{ stabilitySummary.uniqueTests }}</strong>
          <span class="metric-note">историй тест-кейсов</span>
        </article>
        <article class="metric-card metric-card--accent">
          <span class="metric-label">Пройдено</span>
          <strong class="metric-value">{{ passRate }}%</strong>
          <span class="metric-note">по всем историческим результатам</span>
        </article>
        <article class="metric-card">
          <span class="metric-label">P95 длительность</span>
          <strong class="metric-value">{{ formatDuration(p95Duration) }}</strong>
          <span class="metric-note">длинный хвост времени выполнения</span>
        </article>
      </div>
    </header>

    <section class="dashboard-filters" aria-label="Фильтры">
      <div class="filters-topline">
        <div class="filters-heading">
          <span class="panel-kicker">Область</span>
          <p>Фильтры влияют на все метрики и виджеты на странице.</p>
        </div>

        <button
          v-if="
            activeTags.length ||
            activeSuite !== 'all' ||
            activeEnvironment !== 'all' ||
            activeSignature !== 'all' ||
            activeDateFrom ||
            activeDateTo
          "
          type="button"
          class="filter-reset"
          @click="resetFilters()"
        >
          Сбросить
        </button>
      </div>

      <div class="filters-grid">
        <label class="filter-field">
          <span>Suite</span>
          <select v-model="activeSuite">
            <option value="all">Все suite</option>
            <option v-for="suite in filterOptions.suites" :key="suite" :value="suite">
              {{ suite }}
            </option>
          </select>
        </label>

        <label class="filter-field">
          <span>Environment</span>
          <select v-model="activeEnvironment">
            <option value="all">Все environment</option>
            <option v-for="environment in filterOptions.environments" :key="environment" :value="environment">
              {{ environment }}
            </option>
          </select>
        </label>

        <label class="filter-field">
          <span>Сигнатура сбоя</span>
          <select v-model="activeSignature">
            <option value="all">Все сигнатуры</option>
            <option v-for="item in failureSignatures" :key="item.signature" :value="item.signature">
              {{ item.signature }}
            </option>
          </select>
        </label>

        <div class="filter-field filter-field--range">
          <span>Период</span>
          <div class="date-range-fields">
            <input v-model="activeDateFrom" :max="dateFromMax" type="date" />
            <span class="date-range-separator">→</span>
            <input v-model="activeDateTo" :min="dateToMin" type="date" />
          </div>
        </div>
      </div>

      <div class="filter-field filter-field--tags">
        <span>Теги</span>
        <div class="tag-filter-list">
          <button
            type="button"
            class="tag-filter-chip"
            :class="{ 'tag-filter-chip--active': activeTags.length === 0 }"
            @click="activeTags = []"
          >
            Все теги
          </button>
          <button
            v-for="tag in filterOptions.tags"
            :key="tag"
            type="button"
            class="tag-filter-chip"
            :class="{ 'tag-filter-chip--active': activeTags.includes(tag) }"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </button>
        </div>
      </div>
    </section>

    <div v-if="historyLoading" class="dashboard-loading">Загрузка history.jsonl…</div>

    <div v-else-if="dashboardError" class="dashboard-error" role="alert">
      <p>{{ dashboardError }}</p>
      <button type="button" class="filter-reset" @click="retryDashboard()">Повторить</button>
    </div>

    <div v-else-if="!filteredRunCount" class="dashboard-empty">
      <p>История прогонов пока не загружена.</p>
      <p>С текущими фильтрами данных нет. Сбрось фильтры или загрузи `history.jsonl`.</p>
    </div>

    <div v-else class="dashboard-grid">
      <DashboardHealthPanel
        :aggregate-stats="aggregateStats"
        :incident-rate="incidentRate"
        :pass-rate="passRate"
        :ring-style="ringStyle"
      />

      <DashboardStabilityPanel
        :aggregate-incidents="aggregateStats.failed + aggregateStats.broken"
        :stability-summary="stabilitySummary"
        @open-bucket="setActiveStabilityBucket($event)"
      />

      <DashboardTrendPanel :trend-points="trendPoints" @open-report="openReport($event)" />

      <DashboardUnstablePanel :top-unstable-tests="topUnstableTests" @select-test="selectTest($event)" />

      <DashboardTestDetailsPanel
        v-if="selectedTestDetails"
        :selected-test-details="selectedTestDetails"
        :normalize-status="normalizeStatus"
      />

      <DashboardFailureSignaturesPanel
        :active-signature="activeSignature"
        :failure-signatures="failureSignatures"
        @toggle-signature="toggleSignature($event)"
      />

      <DashboardTagHealthPanel :active-tags="activeTags" :tag-health="tagHealth" @toggle-tag="toggleTag($event)" />

      <DashboardRecentReportsPanel :recent-reports="recentReports" @open-report="openReport($event)" />

      <DashboardProblemRunsPanel
        :selected-report-id="selectedReportId"
        :top-problem-runs="topProblemRuns"
        @open-report="openReport($event)"
      />
    </div>

    <DashboardStabilityModal
      v-if="stabilityDialog"
      :items="filteredStabilityDialogItems"
      :search="stabilitySearch"
      :title="stabilityDialog.title"
      @close="setActiveStabilityBucket(null)"
      @select-test="selectTest($event)"
      @update-search="setStabilitySearch($event)"
    />
  </section>
</template>

<style src="../../../assets/style/components/reports/ReportsDashboard.css"></style>
