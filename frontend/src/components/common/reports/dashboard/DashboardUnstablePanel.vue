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
        <span class="panel-kicker">Unstable</span>
        <h3>Самые нестабильные тесты</h3>
        <p class="panel-hint">Нажми на тест, чтобы открыть Test Details</p>
      </div>
    </div>

    <div class="unstable-list">
      <div
        v-for="item in topUnstableTests"
        :key="item.key"
        class="unstable-row"
        @click="emit('selectTest', item.key)"
      >
        <div class="unstable-copy">
          <div class="unstable-name">{{ item.name }}</div>
          <div class="unstable-meta">
            {{ item.totalRuns }} runs · passed {{ item.passedRuns }} · failed {{ item.failedRuns }} · broken {{ item.brokenRuns }} · last {{ item.lastStatus }}
          </div>
        </div>
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
      </div>
    </div>
  </article>
</template>
