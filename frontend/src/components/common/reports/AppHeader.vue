<script setup lang="ts">
type Theme = 'dark' | 'light'

const props = defineProps<{
  sidebarVisible: boolean
  showSidebarToggle?: boolean
  theme: Theme
  uploading: boolean
}>()

const emit = defineEmits<{
  'toggle-sidebar': []
  'toggle-theme': []
  'upload-report': [event: Event]
}>()
</script>

<template>
  <header class="app-header">
    <div class="app-header-brand">
      <img
        class="app-logo"
        :src="props.theme === 'dark' ? '/logo-horizontal-dark.svg' : '/logo-horizontal-light.svg'"
        alt="TestReport Storage"
      />
      <p class="app-subtitle">Хранилище и просмотр отчетов тестов</p>
      <nav class="app-nav" aria-label="Primary">
        <RouterLink class="app-nav-link" :to="{ name: 'dashboard' }">
          Dashboard
        </RouterLink>
        <RouterLink class="app-nav-link" :to="{ name: 'reports' }">
          Reports
        </RouterLink>
      </nav>
    </div>
    <div class="header-actions">
      <button
        v-if="showSidebarToggle !== false"
        class="text-button header-toggle"
        type="button"
        @click="emit('toggle-sidebar')"
      >
        {{ sidebarVisible ? 'Скрыть список' : 'Показать список' }}
      </button>
      <label class="theme-toggle" :title="theme === 'dark' ? 'Тёмная тема' : 'Светлая тема'">
        <input
          type="checkbox"
          :checked="theme === 'light'"
          @change="emit('toggle-theme')"
        />
        <span class="theme-toggle-track">
          <span class="theme-toggle-thumb" />
        </span>
        <span class="theme-toggle-label">
          {{ theme === 'dark' ? 'Тёмная' : 'Светлая' }}
        </span>
      </label>
      <label class="upload-button">
        <span>{{ uploading ? 'Загрузка...' : 'Загрузить отчет (ZIP)' }}</span>
        <input
          type="file"
          accept=".zip"
          :disabled="uploading"
          @change="emit('upload-report', $event)"
        />
      </label>
    </div>
  </header>
</template>

<style scoped src="../../../assets/style/components/reports/AppHeader.css"></style>
