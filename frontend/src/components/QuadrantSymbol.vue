<script setup>
const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['triangle', 'circle', 'square', 'diamond'].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
})
</script>

<template>
  <span
    class="quadrant-symbol"
    :class="`quadrant-symbol--${props.size}`"
    aria-hidden="true"
  >
    <svg viewBox="0 0 16 16" focusable="false">
      <path v-if="props.type === 'triangle'" d="M8 3.1 12.75 11.65H3.25Z" />
      <circle v-else-if="props.type === 'circle'" cx="8" cy="8" r="4.25" />
      <rect
        v-else-if="props.type === 'square'"
        x="3.85"
        y="3.85"
        width="8.3"
        height="8.3"
        rx="0.75"
      />
      <path v-else d="M8 3.15 12.85 8 8 12.85 3.15 8Z" />
    </svg>
  </span>
</template>

<style scoped>
.quadrant-symbol {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--quadrant-symbol-color, var(--color-primary));
  line-height: 0;
}

.quadrant-symbol svg {
  display: block;
  fill: currentColor;
}

.quadrant-symbol--sm {
  width: 14px;
  height: 14px;
  flex: 0 0 14px;
}

.quadrant-symbol--sm svg {
  width: 11px;
  height: 11px;
}

.quadrant-symbol--md {
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
}

.quadrant-symbol--md svg {
  width: 14px;
  height: 14px;
}

.quadrant-symbol--lg {
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
}

.quadrant-symbol--lg svg {
  width: 16px;
  height: 16px;
}
</style>
