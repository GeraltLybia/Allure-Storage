<script setup lang="ts">
import type { ProblemRunItem } from './types'
import type { Report } from '../../../../types/reports'

defineProps<{
  getReportTitle: (report: Report) => string | undefined
  selectedReportId: string | null
  topProblemRuns: ProblemRunItem[]
}>()

const emit = defineEmits<{
  openReport: [id: string]
}>()
</script>

<template>
  <article class="panel panel--span-4">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Attention</span>
        <h3>Проблемные прогоны</h3>
      </div>
    </div>

    <div class="problem-list">
      <button
        v-for="item in topProblemRuns"
        :key="item.report.id"
        class="problem-row"
        type="button"
        :class="{ 'problem-row--selected': item.report.id === selectedReportId }"
        @click="emit('openReport', item.report.id)"
      >
        <div>
          <div class="problem-name">
            {{ getReportTitle(item.report) ?? item.report.id }}
          </div>
          <div class="problem-meta">
            Failed {{ item.report.stats?.failed ?? 0 }} · Broken {{ item.report.stats?.broken ?? 0 }}
          </div>
        </div>
        <strong>{{ item.incidents }}</strong>
      </button>
    </div>
  </article>
</template>
