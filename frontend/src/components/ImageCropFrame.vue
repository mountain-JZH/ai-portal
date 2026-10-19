<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
const props = defineProps({ section: { type: Object, required: true }, image: { type: String, default: '' } })
const emit = defineEmits(['scaleChange'])
const host = ref(null)
const available = ref(0)
const scale = computed(() => Math.min(1, available.value / props.section.width))
let observer
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    available.value = entry.contentRect.width
    emit('scaleChange', scale.value)
  })
  observer.observe(host.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div ref="host" class="image-frame-host" :style="{ maxWidth: `${section.width}px`, height: `${section.height * scale}px` }">
    <div class="image-frame-canvas" :style="{ width: `${section.width}px`, height: `${section.height}px`, transform: `scale(${scale})` }">
      <slot name="background"><img v-if="image" :src="image" alt=""></slot>
    </div>
    <slot :scale="scale" />
  </div>
</template>

<style scoped>
.image-frame-host { position: relative; width: 100%; min-width: 0; overflow: hidden; border-radius: 12px; background: #f5f6f7; }
.image-frame-canvas { position: absolute; top: 0; left: 0; overflow: hidden; isolation: isolate; transform-origin: top left; }
img { width: 100%; height: 100%; object-fit: cover; }
</style>
