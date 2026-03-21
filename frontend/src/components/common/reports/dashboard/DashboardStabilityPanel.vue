<script setup lang="ts">
import type { StabilityBucketKey, StabilitySummary } from './types'

defineProps<{
  aggregateIncidents: number
  stabilitySummary: StabilitySummary
}>()

const emit = defineEmits<{
  openBucket: [bucket: StabilityBucketKey]
}>()
</script>

<template>
  <article class="panel panel--span-8">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Stability</span>
        <h3>Auto QA метрики</h3>
      </div>
    </div>

    <div class="qa-score-list">
      <button class="qa-score" type="button" @click="emit('openBucket', 'flaky')">
        <span>Flaky tests</span>
        <strong>{{ stabilitySummary.flaky }}</strong>
      </button>
      <button class="qa-score" type="button" @click="emit('openBucket', 'alwaysFailed')">
        <span>Always failed</span>
        <strong>{{ stabilitySummary.alwaysFailed }}</strong>
      </button>
      <button class="qa-score" type="button" @click="emit('openBucket', 'alwaysPassed')">
        <span>Always passed</span>
        <strong>{{ stabilitySummary.alwaysPassed }}</strong>
      </button>
      <button class="qa-score" type="button" @click="emit('openBucket', 'incidents')">
        <span>Incidents</span>
        <strong>{{ aggregateIncidents }}</strong>
      </button>
    </div>
  </article>
</template>
