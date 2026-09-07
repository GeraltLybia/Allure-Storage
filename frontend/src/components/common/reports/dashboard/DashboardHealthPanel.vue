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
        <span class="panel-kicker">Состояние</span>
        <h3>Общая стабильность</h3>
      </div>
      <span class="panel-badge">риск {{ incidentRate }}%</span>
    </div>

    <div class="health-layout">
      <div class="health-ring" :style="ringStyle">
        <div class="health-ring-center">
          <strong>{{ passRate }}%</strong>
          <span>пройдено</span>
        </div>
      </div>

      <div class="health-legend">
        <div class="legend-row">
          <span class="legend-dot legend-dot--passed"></span>
          <span>Пройдено</span>
          <strong>{{ aggregateStats.passed }}</strong>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot--failed"></span>
          <span>Сбоя</span>
          <strong>{{ aggregateStats.failed }}</strong>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot--broken"></span>
          <span>Сломано</span>
          <strong>{{ aggregateStats.broken }}</strong>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot--flaky"></span>
          <span>Нестабильно</span>
          <strong>{{ aggregateStats.flaky }}</strong>
        </div>
      </div>
    </div>
  </article>
</template>
