<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import ToolGrid from './ToolGrid.vue'
import '../assets/homepage.css'

defineProps({ tool: { type: Object, required: true }, image: { type: String, default: '' } })
const host = ref(null)
const scale = ref(1)
let observer
onMounted(() => {
  observer = new ResizeObserver(([entry]) => { scale.value = Math.min(1, entry.contentRect.width / 288) })
  observer.observe(host.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<template>
  <div ref="host" class="masthead-preview-theme tool-preview-host" :style="{ height: `${288 * scale}px` }">
    <div class="tool-preview-canvas" :style="{ transform: `scale(${scale})` }">
      <ToolGrid home :preview-tool="tool" :background-images="{ [tool.id]: image }" />
    </div>
  </div>
</template>

<style scoped>
.tool-preview-host { position: relative; width: 100%; max-width: 288px; min-width: 0; }
.tool-preview-canvas { position: absolute; top: 0; left: 0; width: 288px; transform-origin: top left; }
</style>
