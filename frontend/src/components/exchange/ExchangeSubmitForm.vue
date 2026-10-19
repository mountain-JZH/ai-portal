<script setup>
import { nextTick, onBeforeUnmount, reactive, ref, shallowRef, watch } from 'vue'
import SectionImageCropper from '../SectionImageCropper.vue'
import { EXCHANGE_CROP, EXCHANGE_DOMAINS, EXCHANGE_TYPES } from '../../utils/exchangeDiscovery'
import { submitExchangeResource } from '../../services/exchange'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close', 'submitted'])
const dialog = ref(null)
const titleInput = ref(null)
const imageButton = ref(null)
const cropHost = ref(null)
const cropping = ref(false)
const cropBusy = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const submitting = ref(false)
const confirmedBlob = shallowRef(null)
const previewUrl = ref('')
const defaults = () => ({
  title: '',
  description: '',
  reason: '',
  domain: EXCHANGE_DOMAINS[0],
  type: '文章',
  tags: '',
  externalUrl: '',
})
const form = reactive(defaults())
let previousFocus = null
let focusVersion = 0

function releaseImage() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  confirmedBlob.value = null
}
function resetForm() {
  cropping.value = false
  cropBusy.value = false
  errorMessage.value = ''
  successMessage.value = ''
  releaseImage()
  Object.assign(form, defaults())
}
watch(
  () => props.open,
  async (open) => {
    const version = ++focusVersion
    if (open) {
      previousFocus = document.activeElement
      resetForm()
      await nextTick()
      if (!props.open || version !== focusVersion) return
      if (!dialog.value.open) dialog.value.showModal()
      titleInput.value?.focus({ preventScroll: true })
    } else {
      if (dialog.value?.open) dialog.value.close()
      resetForm()
      if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true })
    }
  },
  { flush: 'post' },
)

async function chooseImage() {
  cropping.value = true
  errorMessage.value = ''
  await nextTick()
  cropHost.value?.querySelector('input[type=file]')?.focus({ preventScroll: true })
}
async function cancelCrop() {
  cropping.value = false
  cropBusy.value = false
  await nextTick()
  imageButton.value?.focus({ preventScroll: true })
}
async function confirmCrop(blob) {
  // Own a separate preview URL; the shared cropper revokes its own URLs on unmount.
  const url = URL.createObjectURL(blob)
  releaseImage()
  confirmedBlob.value = blob
  previewUrl.value = url
  await cancelCrop()
}
function close() {
  if (submitting.value) return
  emit('close')
}
function cancelDialog(event) {
  event.preventDefault()
  if (submitting.value) return
  if (cropping.value) cancelCrop()
  else close()
}
async function submit() {
  if (submitting.value || cropping.value || cropBusy.value) return
  submitting.value = true
  errorMessage.value = ''
  const version = focusVersion
  try {
    const resource = await submitExchangeResource({ ...form, imageBlob: confirmedBlob.value })
    if (version !== focusVersion) return
    successMessage.value = `分享成功 · ${resource.displayNumber}`
    emit('submitted', resource)
  } catch (error) {
    if (version === focusVersion) errorMessage.value = error.message || '分享提交失败，请稍后重试。'
  } finally {
    if (version === focusVersion) submitting.value = false
  }
}
onBeforeUnmount(() => {
  focusVersion += 1
  if (dialog.value?.open) dialog.value.close()
  releaseImage()
  if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true })
})
</script>

<template>
  <dialog
    id="share-dialog"
    ref="dialog"
    class="exchange-dialog"
    aria-labelledby="share-title"
    @cancel="cancelDialog"
    @close="close"
  >
    <div class="dialog-top">
      <h2 id="share-title">{{ cropping ? '分享封面 · 图片取景' : '分享发现' }}</h2>
      <button
        class="close"
        type="button"
        :disabled="submitting"
        :aria-label="cropping ? '取消图片取景' : '关闭分享表单'"
        @click="cropping ? cancelCrop() : close()"
      >
        ×
      </button>
    </div>
    <div v-if="cropping" ref="cropHost" class="exchange-crop">
      <SectionImageCropper
        :section="EXCHANGE_CROP"
        local-only
        @cancel="cancelCrop"
        @confirmed="confirmCrop"
        @busy-change="cropBusy = $event"
      />
    </div>
    <div v-else-if="successMessage" class="share-form">
      <p role="status">{{ successMessage }}</p>
      <div class="form-actions">
        <button type="button" class="control primary" @click="close">完成</button>
      </div>
    </div>
    <form v-else class="share-form" :aria-busy="submitting" @submit.prevent="submit">
      <p class="form-hint" role="note">请勿上传公司敏感信息或未经授权公开的资料。</p>
      <label
        >标题<input
          ref="titleInput"
          v-model="form.title"
          required
          maxlength="90"
          placeholder="给这个发现一个清楚的标题"
      /></label>
      <label
        >内容描述<textarea
          v-model="form.description"
          required
          maxlength="1500"
          placeholder="它是什么，有哪些值得了解的内容？"
        />
      </label>
      <div class="form-pair">
        <label
          >推荐领域<select v-model="form.domain">
            <option v-for="domain in EXCHANGE_DOMAINS" :key="domain">{{ domain }}</option>
          </select></label
        >
        <label
          >资源类型<select v-model="form.type">
            <option v-for="type in EXCHANGE_TYPES" :key="type">{{ type }}</option>
          </select></label
        >
      </div>
      <label
        >推荐原因（可选）<textarea
          v-model="form.reason"
          maxlength="600"
          placeholder="你为什么想把它分享给同事？"
        />
      </label>
      <label
        >关键词（可选，用中文或英文逗号分隔）<input
          v-model="form.tags"
          maxlength="100"
          placeholder="例如：巡检，自动化，工作方法"
      /></label>
      <label
        >资源链接（可选，仅 http / https）<input
          v-model="form.externalUrl"
          type="url"
          placeholder="https://…"
      /></label>
      <div class="share-image-actions">
        <button
          ref="imageButton"
          type="button"
          class="control"
          :disabled="submitting"
          @click="chooseImage"
        >
          {{ previewUrl ? '重新选择图片' : '选择本地图片（可选）' }}
        </button>
      </div>
      <p class="form-hint">
        JPG / PNG / WebP，最大 5MB。11:10 取景，输出 1320 × 1200 WebP；确认后才替换封面。
      </p>
      <img v-if="previewUrl" class="file-preview" :src="previewUrl" alt="待分享的本地封面预览" />
      <p v-if="previewUrl" class="form-hint">
        已取景 · 1320 × 1200 / WebP / {{ Math.round(confirmedBlob.size / 1024) }} KB · 未上传
      </p>
      <div v-if="previewUrl" class="share-image-actions">
        <button type="button" class="control" :disabled="submitting" @click="releaseImage">
          清除图片
        </button>
      </div>
      <p class="form-error" role="alert">{{ errorMessage }}</p>
      <div class="form-actions">
        <button type="button" class="control" :disabled="submitting" @click="close">取消</button>
        <button type="submit" class="control primary" :disabled="submitting">
          {{ submitting ? '提交中…' : '提交' }}
        </button>
      </div>
    </form>
  </dialog>
</template>
