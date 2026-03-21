<script setup lang="ts">
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
</script>

<template>
  <div class="dashboard-modal-backdrop" @click.self="emit('close')">
    <div class="dashboard-modal">
      <div class="dashboard-modal-header">
        <div>
          <span class="panel-kicker">Stability</span>
          <h3>{{ title }}</h3>
        </div>
        <button type="button" class="dashboard-modal-close" @click="emit('close')">
          Закрыть
        </button>
      </div>

      <input
        :value="search"
        type="search"
        class="dashboard-modal-search"
        placeholder="Найти тест по имени"
        @input="emit('updateSearch', ($event.target as HTMLInputElement).value)"
      />

      <div v-if="items.length" class="dashboard-modal-list">
        <div
          v-for="item in items"
          :key="item.key"
          class="dashboard-modal-row"
          @click="emit('selectTest', item.key)"
        >
          <div class="dashboard-modal-row-main">
            <div class="dashboard-modal-row-title">{{ item.name }}</div>
            <div class="dashboard-modal-row-meta">
              last {{ item.lastStatus }} · {{ item.incidents }} incidents · {{ item.totalRuns }} runs
            </div>
          </div>
          <strong>{{ item.incidents }}</strong>
        </div>
      </div>
      <p v-else class="panel-empty">Для текущего набора фильтров список пуст.</p>
    </div>
  </div>
</template>
