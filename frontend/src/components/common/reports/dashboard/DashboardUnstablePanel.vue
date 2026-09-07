<script setup lang="ts">
import type { UnstableTest } from './types'

defineProps<{
  topUnstableTests: UnstableTest[]
}>()

const emit = defineEmits<{
  selectTest: [key: string]
}>()
</script>

<template>
  <article class="panel panel--span-8">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Нестабильность</span>
        <h3>Самые нестабильные тесты</h3>
        <p class="panel-hint">Нажми на тест, чтобы открыть детали</p>
      </div>
    </div>

    <div class="unstable-list">
      <button
        v-for="item in topUnstableTests"
        :key="item.key"
        class="unstable-row"
        type="button"
        @click="emit('selectTest', item.key)"
      >
        <span class="unstable-name">{{ item.name }}</span>
        <span class="unstable-stats">
          {{ item.totalRuns }} прогонов · пройдено {{ item.passedRuns }} · сбоя {{ item.failedRuns }} · сломано
          {{ item.brokenRuns }} · последний {{ item.lastStatus }}
        </span>
        <div class="unstable-bar">
          <div
            class="unstable-bar-segment unstable-bar-segment--passed"
            :style="{ width: `${item.totalRuns ? Math.round((item.passedRuns / item.totalRuns) * 100) : 0}%` }"
          ></div>
          <div
            class="unstable-bar-segment unstable-bar-segment--failed"
            :style="{ width: `${item.totalRuns ? Math.round((item.failedRuns / item.totalRuns) * 100) : 0}%` }"
          ></div>
          <div
            class="unstable-bar-segment unstable-bar-segment--broken"
            :style="{ width: `${item.totalRuns ? Math.round((item.brokenRuns / item.totalRuns) * 100) : 0}%` }"
          ></div>
        </div>
        <strong>{{ item.stability }}%</strong>
      </button>
    </div>
  </article>
</template>
