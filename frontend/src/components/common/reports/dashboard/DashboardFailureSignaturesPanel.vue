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
        <span class="panel-kicker">Failures</span>
        <h3>Failure signatures</h3>
        <p class="panel-hint">Нажми на сигнатуру, чтобы отфильтровать dashboard</p>
      </div>
    </div>

    <div class="signature-list">
      <div
        v-for="item in failureSignatures"
        :key="item.signature"
        class="signature-row"
        :class="{ 'signature-row--active': activeSignature === item.signature }"
        @click="emit('toggleSignature', item.signature)"
      >
        <span class="signature-text">{{ item.signature }}</span>
        <strong>{{ item.count }}</strong>
      </div>
    </div>
  </article>
</template>
