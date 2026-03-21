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
        <span class="panel-kicker">Tags</span>
        <h3>Health по тегам</h3>
      </div>
    </div>

    <div class="tag-list">
      <div
        v-for="item in tagHealth"
        :key="item.tag"
        class="tag-row"
        :class="{ 'tag-row--active': activeTags.includes(item.tag) }"
        @click="emit('toggleTag', item.tag)"
      >
        <div class="tag-meta">
          <span class="tag-name">{{ item.tag }}</span>
          <span class="tag-caption">{{ item.total }} runs · {{ item.incidents }} incidents</span>
        </div>
        <div class="tag-bar">
          <div class="tag-bar-fill" :style="{ width: `${item.healthyRate}%` }"></div>
        </div>
        <strong>{{ item.healthyRate }}%</strong>
      </div>
    </div>
  </article>
</template>
