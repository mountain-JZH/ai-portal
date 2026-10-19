<script setup>
defineProps({
  direction: { type: String, default: 'right', validator: (value) => ['left', 'right'].includes(value) },
  size: { type: Number, default: 18 },
})
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path :d="direction === 'left' ? 'm15 6-6 6 6 6' : 'm9 6 6 6-6 6'" />
  </svg>
</template>

<style scoped>
svg { display: block; flex-shrink: 0; }
</style>
