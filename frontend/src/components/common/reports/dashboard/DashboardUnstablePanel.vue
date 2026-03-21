<script setup lang="ts">
import type { UnstableTest } from './types'

defineProps<{
  topUnstableTests: UnstableTest[]
}>()
</script>

<template>
  <article class="panel panel--span-8">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Unstable</span>
        <h3>Самые нестабильные тесты</h3>
      </div>
    </div>

    <div class="unstable-list">
      <div
        v-for="item in topUnstableTests"
        :key="item.key"
        class="unstable-row"
      >
        <div class="unstable-copy">
          <div class="unstable-name">{{ item.name }}</div>
          <div class="unstable-meta">
            {{ item.incidents }} incidents · {{ item.totalRuns }} runs · last {{ item.lastStatus }}
          </div>
        </div>
        <div class="unstable-bar">
          <div class="unstable-bar-fill" :style="{ width: `${item.stability}%` }"></div>
        </div>
        <strong>{{ item.stability }}%</strong>
      </div>
    </div>
  </article>
</template>
