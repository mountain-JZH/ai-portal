<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import SectionMasthead from './SectionMasthead.vue'
import '../assets/homepage.css'

const props = defineProps({
  section: { type: Object, required: true },
  image: { type: String, default: '' },
  fallbackImage: { type: String, default: '' },
  textMode: { type: String, default: 'dark' },
})
const emit = defineEmits(['scaleChange'])
const host = ref(null)
const availableWidth = ref(0)
const scale = computed(() => Math.min(1, availableWidth.value / props.section.width))
let observer
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    availableWidth.value = entry.contentRect.width
    emit('scaleChange', scale.value)
  })
  observer.observe(host.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div ref="host" class="masthead-preview-theme preview-host" :style="{ height: `${section.height * scale}px` }">
    <div class="preview-canvas" :style="{ width: `${section.width}px`, height: `${section.height}px`, transform: `scale(${scale})` }">
      <SectionMasthead preview :title="section.title" :description="section.description" :to="section.to"
        :image="image" :fallback-image="fallbackImage" :text-mode="textMode"
        :navigation-label="section.navigationLabel" :navigation-aria-label="section.navigationAriaLabel">
        <template v-if="$slots.background" #background><slot name="background" /></template>
      </SectionMasthead>
    </div>
    <slot :scale="scale" />
  </div>
</template>

<style scoped>
.preview-host { position: relative; width: 100%; min-width: 0; overflow: hidden; border-radius: 12px; background: #f5f6f7; }
.preview-canvas { position: absolute; top: 0; left: 0; transform-origin: top left; }
</style>
