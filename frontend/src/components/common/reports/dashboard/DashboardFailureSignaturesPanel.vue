<script setup lang="ts">
import type { FailureSignature } from './types'

defineProps<{
  activeSignature: string
  failureSignatures: FailureSignature[]
}>()

const emit = defineEmits<{
  toggleSignature: [signature: string]
}>()
</script>

<template>
  <article class="panel panel--span-4">
    <div class="panel-header">
      <div>
        <span class="panel-kicker">Сбои</span>
        <h3>Сигнатуры сбоев</h3>
        <p class="panel-hint">Нажми на сигнатуру, чтобы отфильтровать панель</p>
      </div>
    </div>

    <div class="signature-list">
      <button
        v-for="item in failureSignatures"
        :key="item.signature"
        class="signature-row"
        type="button"
        :class="{ 'signature-row--active': activeSignature === item.signature }"
        @click="emit('toggleSignature', item.signature)"
      >
        <span class="signature-text">{{ item.signature }}</span>
        <strong>{{ item.count }}</strong>
      </button>
    </div>
  </article>
</template>
