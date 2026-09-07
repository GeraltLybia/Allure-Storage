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
        <span class="panel-kicker">Стабильность</span>
        <h3>Auto QA метрики</h3>
      </div>
    </div>

    <div class="qa-score-list">
      <button class="qa-score qa-score--flaky" type="button" @click="emit('openBucket', 'flaky')">
        <span>Нестабильные тесты</span>
        <strong>{{ stabilitySummary.flaky }}</strong>
      </button>
      <button class="qa-score qa-score--failed" type="button" @click="emit('openBucket', 'alwaysFailed')">
        <span>Всегда падают</span>
        <strong>{{ stabilitySummary.alwaysFailed }}</strong>
      </button>
      <button class="qa-score qa-score--passed" type="button" @click="emit('openBucket', 'alwaysPassed')">
        <span>Всегда проходят</span>
        <strong>{{ stabilitySummary.alwaysPassed }}</strong>
      </button>
      <button class="qa-score qa-score--incidents" type="button" @click="emit('openBucket', 'incidents')">
        <span>Инциденты</span>
        <strong>{{ aggregateIncidents }}</strong>
      </button>
    </div>
  </article>
</template>
