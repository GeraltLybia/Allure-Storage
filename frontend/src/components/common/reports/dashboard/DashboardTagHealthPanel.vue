<script setup lang="ts">
import type { TagHealth } from './types'

defineProps<{
  activeTags: string[]
  tagHealth: TagHealth[]
}>()

const emit = defineEmits<{
  toggleTag: [tag: string]
}>()
</script>

<template>
  <article class="panel panel--span-4">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Теги</span>
        <h3>Состояние по тегам</h3>
        <p class="panel-hint">Нажми на тег, чтобы включить фильтр</p>
      </div>
    </div>

    <div class="tag-list">
      <button
        v-for="item in tagHealth"
        :key="item.tag"
        class="tag-row"
        type="button"
        :class="{ 'tag-row--active': activeTags.includes(item.tag) }"
        @click="emit('toggleTag', item.tag)"
      >
        <span class="tag-name">{{ item.tag }}</span>
        <span class="tag-caption">
          {{ item.total }} прогонов · пройдено {{ item.passedRuns }} · сбоя {{ item.failedRuns }} · сломано
          {{ item.brokenRuns }}
        </span>
        <div class="tag-bar">
          <div
            class="tag-bar-segment tag-bar-segment--passed"
            :style="{ width: `${item.total ? Math.round((item.passedRuns / item.total) * 100) : 0}%` }"
          ></div>
          <div
            class="tag-bar-segment tag-bar-segment--failed"
            :style="{ width: `${item.total ? Math.round((item.failedRuns / item.total) * 100) : 0}%` }"
          ></div>
          <div
            class="tag-bar-segment tag-bar-segment--broken"
            :style="{ width: `${item.total ? Math.round((item.brokenRuns / item.total) * 100) : 0}%` }"
          ></div>
        </div>
        <strong>{{ item.healthyRate }}%</strong>
      </button>
    </div>
  </article>
</template>
