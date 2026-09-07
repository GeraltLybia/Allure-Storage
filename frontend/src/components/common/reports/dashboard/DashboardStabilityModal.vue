<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import type { StabilityDetailItem } from './types'

defineProps<{
  items: StabilityDetailItem[]
  search: string
  title: string
}>()

const emit = defineEmits<{
  close: []
  selectTest: [key: string]
  updateSearch: [value: string]
}>()

const searchInput = ref<HTMLInputElement | null>(null)

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  void nextTick(() => searchInput.value?.focus())
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="dashboard-modal-backdrop" @click.self="emit('close')">
    <div class="dashboard-modal" role="dialog" aria-modal="true" :aria-label="title">
      <div class="dashboard-modal-header">
        <div>
          <span class="panel-kicker">Стабильность</span>
          <h3>{{ title }}</h3>
        </div>
        <button type="button" class="dashboard-modal-close" aria-label="Закрыть" @click="emit('close')">Закрыть</button>
      </div>

      <input
        ref="searchInput"
        :value="search"
        type="search"
        class="dashboard-modal-search"
        placeholder="Найти тест по имени"
        aria-label="Найти тест по имени"
        @input="emit('updateSearch', ($event.target as HTMLInputElement).value)"
      />

      <div v-if="items.length" class="dashboard-modal-list">
        <button
          v-for="item in items"
          :key="item.key"
          class="dashboard-modal-row"
          type="button"
          @click="emit('selectTest', item.key)"
        >
          <div class="dashboard-modal-row-main">
            <div class="dashboard-modal-row-title">{{ item.name }}</div>
            <div class="dashboard-modal-row-meta">
              последний {{ item.lastStatus }} · {{ item.incidents }} инцидентов · {{ item.totalRuns }} прогонов
            </div>
          </div>
          <strong>{{ item.incidents }}</strong>
        </button>
      </div>
      <p v-else class="panel-empty">Для текущего набора фильтров список пуст.</p>
    </div>
  </div>
</template>
