<script setup lang="ts">
import type { HistoryPoint } from './types'

defineProps<{
  trendPoints: HistoryPoint[]
}>()

const emit = defineEmits<{
  openReport: [id: string]
}>()
</script>

<template>
  <article class="panel panel--span-12">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Trend</span>
        <h3>Последние прогоны</h3>
      </div>
    </div>

    <div class="run-trend-list">
      <div
        v-for="point in trendPoints"
        :key="point.key"
        class="run-trend-row"
      >
        <button
          v-if="point.reportId"
          type="button"
          class="run-trend-link"
          @click="emit('openReport', point.reportId)"
        >
          {{ point.label }}
        </button>
        <span v-else class="run-trend-name">{{ point.label }}</span>
        <div class="run-trend-bar">
          <div
            class="run-trend-segment run-trend-segment--passed"
            :style="{ width: `${point.total ? Math.round((point.passed / point.total) * 100) : 0}%` }"
          ></div>
          <div
            class="run-trend-segment run-trend-segment--failed"
            :style="{ width: `${point.total ? Math.round((point.failed / point.total) * 100) : 0}%` }"
          ></div>
          <div
            class="run-trend-segment run-trend-segment--broken"
            :style="{ width: `${point.total ? Math.round((point.broken / point.total) * 100) : 0}%` }"
          ></div>
        </div>
        <span class="run-trend-meta">{{ point.total }} tests</span>
        <strong>{{ point.passRate }}%</strong>
      </div>
    </div>
  </article>
</template>
