<script setup>
import { computed } from 'vue'
import { projectUpdateLabel } from '../utils/projectUpdates'
import { importTime } from '../utils/projectDisplay'
const props = defineProps({
  at: { type: String, default: null },
  now: { type: Date, default: () => new Date() },
})
const label = computed(() => projectUpdateLabel(props.at, props.now))
const today = computed(() => label.value === '今日更新')
</script>

<template>
  <time
    v-if="label"
    class="project-update-badge"
    :class="{ 'is-today': today }"
    :datetime="at"
    :title="`最近修改（北京时间）：${importTime(at)}`"
  >
    {{ label }}
  </time>
</template>

<style scoped>
.project-update-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  flex-shrink: 0;
  height: 24px;
  padding: 0 10px;
  border: 1px solid #efd9a5;
  border-radius: 6px;
  background: #fff3d8;
  font-size: 12px;
  font-weight: 600;
  line-height: 20px;
  letter-spacing: normal;
  color: var(--ink, #22292c);
  white-space: nowrap;
}
.project-update-badge.is-today {
  border-color: var(--yellow, #f7b334);
  background: var(--yellow, #f7b334);
}
</style>
