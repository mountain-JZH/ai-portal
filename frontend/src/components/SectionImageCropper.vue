<script setup>
import { computed, onUnmounted, ref, shallowRef } from 'vue'
import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'
import { cropGeometry, exportSectionCrop, IMAGE_TYPES, MAX_IMAGE_BYTES } from '../utils/sectionImageCrop'
import MastheadPreview from './MastheadPreview.vue'
import ImageCropFrame from './ImageCropFrame.vue'

const props = defineProps({
  section: { type: Object, required: true },
  textMode: { type: String, default: 'dark' },
  localOnly: { type: Boolean, default: false },
})
const emit = defineEmits(['cancel', 'saved', 'busyChange', 'confirmed'])
const image = shallowRef(null)
const originalUrl = ref('')
const resultUrl = ref('')
const resultBlob = shallowRef(null)
const zoom = ref(1)
const x = ref(0)
const y = ref(0)
const previewScale = ref(1)
const phase = ref('choose')
const busy = ref('')
const errorMessage = ref('')
let selectionVersion = 0
let drag = null

const geometry = computed(() => image.value
  ? cropGeometry(image.value.naturalWidth, image.value.naturalHeight,
    props.section.width, props.section.height, zoom.value, x.value, y.value) : null)
const imageStyle = computed(() => geometry.value ? {
  position: 'absolute', zIndex: -1, maxWidth: 'none',
  width: `${geometry.value.width}px`, height: `${geometry.value.height}px`,
  left: `${geometry.value.left}px`, top: `${geometry.value.top}px`,
} : {})
const lowResolution = computed(() => geometry.value && (
  geometry.value.sourceWidth < props.section.outputWidth || geometry.value.sourceHeight < props.section.outputHeight
))

function setBusy(value) { busy.value = value; emit('busyChange', Boolean(value)) }
function releaseResult() {
  if (resultUrl.value) URL.revokeObjectURL(resultUrl.value)
  resultUrl.value = ''
  resultBlob.value = null
}
function reset() {
  zoom.value = 1
  x.value = 0
  y.value = 0
  drag = null
}
function clampPosition() {
  if (!geometry.value) return
  const next = geometry.value
  x.value = next.x
  y.value = next.y
}

async function selectFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || busy.value) return
  errorMessage.value = ''
  if (!IMAGE_TYPES.includes(file.type)) { errorMessage.value = '请选择 JPG、PNG 或 WebP 图片'; return }
  if (file.size > MAX_IMAGE_BYTES) { errorMessage.value = '原始图片不能超过 5MB'; return }
  const version = ++selectionVersion
  const url = URL.createObjectURL(file)
  setBusy('正在读取图片…')
  try {
    const decoded = new Image()
    decoded.src = url
    await decoded.decode()
    if (version !== selectionVersion) return
    const { naturalWidth: width, naturalHeight: height } = decoded
    if (!width || !height || Math.max(width, height) > 8192 || width * height > 16_000_000) {
      throw new Error('原图尺寸不得超过 8192px，像素总量不得超过 1600 万')
    }
    if (originalUrl.value) URL.revokeObjectURL(originalUrl.value)
    releaseResult()
    originalUrl.value = url
    image.value = decoded
    phase.value = 'crop'
    reset()
  } catch (error) {
    if (version === selectionVersion) errorMessage.value = error.message || '图片无法解码，请选择其他图片'
  } finally {
    if (originalUrl.value !== url) URL.revokeObjectURL(url)
    if (version === selectionVersion) setBusy('')
  }
}

function pointerDown(event) {
  if (busy.value || !geometry.value || (event.pointerType === 'mouse' && event.button !== 0)) return
  drag = { pointer: event.pointerId, clientX: event.clientX, clientY: event.clientY, x: geometry.value.x, y: geometry.value.y }
  event.currentTarget.setPointerCapture(event.pointerId)
  event.currentTarget.focus()
}
function pointerMove(event) {
  if (!drag || drag.pointer !== event.pointerId || !previewScale.value) return
  x.value = drag.x + (event.clientX - drag.clientX) / previewScale.value
  y.value = drag.y + (event.clientY - drag.clientY) / previewScale.value
  clampPosition()
}
function pointerEnd(event) {
  if (drag?.pointer === event.pointerId) drag = null
}
function moveWithKeys(event) {
  const delta = { ArrowLeft: [-8, 0], ArrowRight: [8, 0], ArrowUp: [0, -8], ArrowDown: [0, 8] }[event.key]
  if (!delta || busy.value) return
  event.preventDefault()
  x.value += delta[0]
  y.value += delta[1]
  clampPosition()
}

async function confirmCrop() {
  if (busy.value || !image.value) return
  errorMessage.value = ''
  setBusy('正在生成裁剪结果…')
  const version = selectionVersion
  try {
    const blob = await exportSectionCrop(image.value, geometry.value, props.section.outputWidth, props.section.outputHeight)
    if (version !== selectionVersion) return
    releaseResult()
    resultBlob.value = blob
    resultUrl.value = URL.createObjectURL(blob)
    phase.value = 'ready'
    if (props.localOnly) emit('confirmed', blob)
  } catch (error) {
    if (version === selectionVersion) errorMessage.value = error.message || '裁剪失败，请重试'
  } finally {
    if (version === selectionVersion) setBusy('')
  }
}

async function save() {
  if (props.localOnly || busy.value || !resultBlob.value) return
  errorMessage.value = ''
  setBusy('正在保存图片…')
  try {
    const body = new FormData()
    body.append('file', new File([resultBlob.value], `${props.section.key}.webp`, { type: 'image/webp' }))
    body.append('textMode', props.textMode)
    const response = await adminFetch(`${API_BASE_URL}/api/admin/section-visuals/${props.section.key}`, { method: 'PUT', body })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `保存失败（${response.status}）`)
    if (data.sectionKey !== props.section.key || !data.image?.startsWith('/uploads/sections/')) throw new Error('服务器返回了无效配置，请重新加载确认')
    emit('saved', data)
  } catch (error) {
    errorMessage.value = error.message || '保存失败，原背景保持不变'
  } finally {
    setBusy('')
  }
}

onUnmounted(() => {
  selectionVersion += 1
  if (originalUrl.value) URL.revokeObjectURL(originalUrl.value)
  releaseResult()
})
</script>

<template>
  <section class="crop-editor" :aria-label="`${section.title}背景取景`" :aria-busy="Boolean(busy)">
    <h2>{{ section.title }} · 更换背景</h2>
    <p>JPG / PNG / WebP，原图最大 5MB。拖动图片或使用方向键调整位置，文字仅供预览，不会写入图片。</p>
    <label class="file-picker">
      {{ image ? '重新选择图片' : '选择本地图片' }}
      <input type="file" accept="image/jpeg,image/png,image/webp" :disabled="Boolean(busy)" @change="selectFile">
    </label>

    <template v-if="image && phase === 'crop'">
      <p class="crop-caption">取景范围 · {{ image.naturalWidth }} × {{ image.naturalHeight }} 原图</p>
      <component :is="localOnly ? ImageCropFrame : MastheadPreview" :section="section" :text-mode="textMode" class="crop-frame" @scale-change="previewScale = $event">
        <template #background><img :src="originalUrl" :style="imageStyle" alt="" draggable="false"></template>
        <template #default>
          <div class="drag-surface" tabindex="0" role="group" aria-label="图片取景，使用方向键或拖动调整位置"
            @pointerdown="pointerDown" @pointermove="pointerMove" @pointerup="pointerEnd" @pointercancel="pointerEnd"
            @lostpointercapture="pointerEnd" @keydown="moveWithKeys" />
        </template>
      </component>
      <label class="zoom-control">缩放 {{ Number(zoom).toFixed(2) }}×
        <input v-model.number="zoom" type="range" min="1" max="4" step="0.01" :disabled="Boolean(busy)" @input="clampPosition">
      </label>
      <p v-if="lowResolution" class="crop-warning" role="status">当前取景的有效分辨率低于推荐输出，放大不会增加真实细节；可以更换图片或减少缩放。</p>
      <div class="editor-actions">
        <button type="button" :disabled="Boolean(busy)" @click="reset">重置</button>
        <button type="button" class="primary" :disabled="Boolean(busy)" @click="confirmCrop">确认取景</button>
      </div>
    </template>

    <template v-if="phase === 'ready'">
      <p class="crop-caption">待保存结果（尚未生效） · {{ section.outputWidth }} × {{ section.outputHeight }} · {{ (resultBlob.size / 1024).toFixed(0) }} KB / WebP</p>
      <component :is="localOnly ? ImageCropFrame : MastheadPreview" :section="section" :image="resultUrl" :text-mode="textMode" />
      <div class="editor-actions">
        <button type="button" :disabled="Boolean(busy)" @click="phase = 'crop'">重新取景</button>
        <button v-if="!localOnly" type="button" class="primary" :disabled="Boolean(busy)" @click="save">保存图片并生效</button>
      </div>
    </template>
    <p v-if="busy" role="status">{{ busy }}</p>
    <p v-if="errorMessage" class="crop-error" role="alert">{{ errorMessage }}。原生效背景未被替换。</p>
    <button type="button" class="cancel" :disabled="Boolean(busy)" @click="emit('cancel')">取消更换</button>
  </section>
</template>

<style scoped>
.crop-editor { min-width: 0; padding: 24px; border: 1px solid #dce1e5; border-radius: 12px; background: #fff; }
h2 { margin: 0 0 12px; font-size: 20px; }
p { color: #586165; font-size: 14px; line-height: 1.7; overflow-wrap: anywhere; }
.file-picker { display: grid; gap: 8px; width: fit-content; max-width: 100%; font-size: 14px; }
input[type=file] { max-width: 100%; }
.crop-caption { margin: 20px 0 12px; font-size: 13px; }
.crop-frame { outline: 1px solid #aab4bc; outline-offset: 2px; }
.drag-surface { position: absolute; inset: 0; cursor: grab; touch-action: none; }
.drag-surface:active { cursor: grabbing; }
.drag-surface:focus-visible { outline: 2px solid #6d5b55; outline-offset: -3px; border-radius: 12px; }
.zoom-control { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-top: 22px; font-size: 14px; }
.zoom-control input { flex: 1; min-width: 100px; accent-color: #6d5b55; }
.editor-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }
button { padding: 10px 16px; border: 1px solid #c9cfd2; border-radius: 8px; background: #fff; color: #22292c; font: inherit; font-size: 14px; cursor: pointer; }
button.primary { background: #f7b334; border-color: #f7b334; }
button:disabled { cursor: wait; opacity: .55; }
button:focus-visible, input:focus-visible { outline: 2px solid #6d5b55; outline-offset: 3px; }
.cancel { margin-top: 20px; }
.crop-warning { color: #785c23; }
.crop-error { color: #b33333; }
@media (max-width: 500px) { .crop-editor { padding: 16px; } }
</style>
