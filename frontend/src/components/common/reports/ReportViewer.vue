<script setup lang="ts">
defineProps<{
  sidebarVisible: boolean
  viewerSrc: string | null
}>()

const emit = defineEmits<{
  showSidebar: []
}>()
</script>

<template>
  <section class="viewer">
    <button v-if="!sidebarVisible" type="button" class="viewer-toggle" @click="emit('showSidebar')">
      Показать список отчетов
    </button>
    <iframe
      v-if="viewerSrc"
      :key="viewerSrc"
      :src="viewerSrc"
      title="Allure report"
      sandbox="allow-scripts allow-popups"
      class="viewer-frame"
    />
    <div v-else class="viewer-placeholder">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M14 3v5h5" />
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
        <path d="M9 13h6" />
        <path d="M9 17h4" />
      </svg>
      <h2>Выберите отчет</h2>
      <p>Список доступных отчетов находится слева.</p>
    </div>
  </section>
</template>

<style scoped src="../../../assets/style/components/reports/ReportViewer.css"></style>
