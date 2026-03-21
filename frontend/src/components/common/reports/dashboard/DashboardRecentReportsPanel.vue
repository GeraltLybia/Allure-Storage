<script setup lang="ts">
import type { RecentReportItem } from './types'

defineProps<{
  recentReports: RecentReportItem[]
}>()

const emit = defineEmits<{
  openReport: [id: string]
}>()
</script>

<template>
  <article class="panel panel--span-8">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Reports</span>
        <h3>Последние отчеты</h3>
      </div>
    </div>

    <div class="trend-list">
      <button
        v-for="report in recentReports"
        :key="report.id"
        class="trend-row"
        type="button"
        :class="{ 'trend-row--active': report.selected }"
        @click="emit('openReport', report.id)"
      >
        <div class="trend-meta">
          <span class="trend-name">{{ report.label }}</span>
          <span class="trend-caption">
            {{ report.total }} tests · {{ report.incidents }} incidents
          </span>
        </div>
        <div class="trend-bar">
          <div class="trend-bar-fill" :style="{ width: `${report.healthy}%` }"></div>
        </div>
        <strong>{{ report.healthy }}%</strong>
      </button>
    </div>
  </article>
</template>
