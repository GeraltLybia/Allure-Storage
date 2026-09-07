<script setup lang="ts">
import { formatDuration } from '../../../../utils/reports'
import type { SelectedTestDetails } from './types'

defineProps<{
  selectedTestDetails: SelectedTestDetails
  normalizeStatus: (value: string | undefined) => string
}>()
</script>

<template>
  <article class="panel panel--span-4">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Детали теста</span>
        <h3>{{ selectedTestDetails.name }}</h3>
      </div>
    </div>

    <div class="test-detail-summary">
      <div class="test-detail-chip">
        <span>Последний статус</span>
        <strong>{{ selectedTestDetails.lastStatus }}</strong>
      </div>
      <div class="test-detail-chip">
        <span>Прогонов</span>
        <strong>{{ selectedTestDetails.totalRuns }}</strong>
      </div>
      <div class="test-detail-chip">
        <span>Инцидентов</span>
        <strong>{{ selectedTestDetails.incidents }}</strong>
      </div>
    </div>

    <div class="test-history-list">
      <div
        v-for="(result, index) in selectedTestDetails.history"
        :key="`${selectedTestDetails.name}-${index}-${result.start ?? 0}`"
        class="test-history-row"
      >
        <div>
          <div class="test-history-status" :class="`test-history-status--${normalizeStatus(result.status)}`">
            {{ normalizeStatus(result.status) }}
          </div>
          <div class="test-history-meta">
            {{ formatDuration(result.duration) }} · {{ result.environment || 'unknown' }}
          </div>
        </div>
        <div class="test-history-message">
          {{ result.message?.split('\n')[0] || 'Без сообщения' }}
        </div>
      </div>
    </div>
  </article>
</template>
