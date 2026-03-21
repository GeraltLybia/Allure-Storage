<script setup lang="ts">
import type { AggregateStats } from './types'

defineProps<{
  aggregateStats: AggregateStats
  incidentRate: number
  passRate: number
  ringStyle: Record<string, string>
}>()
</script>

<template>
  <article class="panel panel--span-4">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Health</span>
        <h3>Общая стабильность</h3>
      </div>
      <span class="panel-badge">risk {{ incidentRate }}%</span>
    </div>

    <div class="health-layout">
      <div class="health-ring" :style="ringStyle">
        <div class="health-ring-center">
          <strong>{{ passRate }}%</strong>
          <span>passed</span>
        </div>
      </div>

      <div class="health-legend">
        <div class="legend-row">
          <span class="legend-dot legend-dot--passed"></span>
          <span>Passed</span>
          <strong>{{ aggregateStats.passed }}</strong>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot--failed"></span>
          <span>Failed</span>
          <strong>{{ aggregateStats.failed }}</strong>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot--broken"></span>
          <span>Broken</span>
          <strong>{{ aggregateStats.broken }}</strong>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot--flaky"></span>
          <span>Flaky status</span>
          <strong>{{ aggregateStats.flaky }}</strong>
        </div>
      </div>
    </div>
  </article>
</template>
