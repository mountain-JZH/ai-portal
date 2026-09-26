<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const route = useRoute()
const isEdit = computed(() => Boolean(route.params.id))
const bannerId = computed(() => String(route.params.id || ''))

function getLocalDateKey() {
  const now = new Date()
  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-')
}

const form = reactive({
  category: '',
  date: getLocalDateKey(),
  title: '',
  description: '',
  buttonText: '',
  image: '',
  actionType: 'route',
  actionTarget: '',
  sortOrder: 0,
  isActive: true,
})

const loading = ref(false)
const notFound = ref(false)
const loadError = ref('')
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const createdId = ref(null)
const isUploading = ref(false)
const uploadMessage = ref('')
const uploadError = ref('')
const uploadStage = ref('idle')
const imageOptimizationInfo = ref(null)
const imagePreviewFailed = ref(false)
const imageInput = ref(null)

const allowedImageTypes = new Set(['image/jpeg', 'image/png', 'image/webp'])
const maxImageSize = 5 * 1024 * 1024
const maxBannerWidth = 1600
const maxBannerHeight = 900
const webpQuality = 0.82
const supportedActionTypes = new Set(['none', 'route', 'external'])

const imagePreviewUrl = computed(() => {
  const image = form.image.trim()

  if (!image) return ''
  if (/^https?:\/\//i.test(image)) return image
  if (image.startsWith('/uploads/')) return `${API_BASE_URL}${image}`

  return image
})

function formatFileSize(size) {
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`

  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function createWebpFileName(originalName) {
  const baseName = originalName.replace(/\.[^.]+$/, '').trim() || 'banner'
  return `${baseName}.webp`
}

async function optimizeBannerImage(file) {
  const objectUrl = URL.createObjectURL(file)
  const image = new Image()

  try {
    await new Promise((resolve, reject) => {
      image.onload = resolve
      image.onerror = () => reject(new Error('图片无法解码，请检查文件是否完整'))
      image.src = objectUrl
    })

    const originalWidth = image.naturalWidth
    const originalHeight = image.naturalHeight

    if (!originalWidth || !originalHeight) {
      throw new Error('无法读取图片尺寸，请重新选择图片')
    }

    const scale = Math.min(
      1,
      maxBannerWidth / originalWidth,
      maxBannerHeight / originalHeight,
    )
    const optimizedWidth = Math.max(1, Math.round(originalWidth * scale))
    const optimizedHeight = Math.max(1, Math.round(originalHeight * scale))
    const canvas = document.createElement('canvas')
    canvas.width = optimizedWidth
    canvas.height = optimizedHeight

    const context = canvas.getContext('2d')
    if (!context) throw new Error('浏览器无法创建图片处理画布')

    context.drawImage(image, 0, 0, optimizedWidth, optimizedHeight)

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (result) => {
          if (result) resolve(result)
          else reject(new Error('图片转换失败，请更换图片后重试'))
        },
        'image/webp',
        webpQuality,
      )
    })

    if (blob.type !== 'image/webp') {
      throw new Error('当前浏览器不支持 WebP 图片转换')
    }

    return {
      file: new File([blob], createWebpFileName(file.name), {
        type: 'image/webp',
        lastModified: Date.now(),
      }),
      originalWidth,
      originalHeight,
      optimizedWidth,
      optimizedHeight,
    }
  } catch (error) {
    if (error instanceof Error) throw error
    throw new Error('图片处理失败，请重新选择图片', { cause: error })
  } finally {
    image.onload = null
    image.onerror = null
    URL.revokeObjectURL(objectUrl)
  }
}

function resetForm() {
  Object.assign(form, {
    category: '',
    date: getLocalDateKey(),
    title: '',
    description: '',
    buttonText: '',
    image: '',
    actionType: 'route',
    actionTarget: '',
    sortOrder: 0,
    isActive: true,
  })
  uploadMessage.value = ''
  uploadError.value = ''
  uploadStage.value = 'idle'
  imageOptimizationInfo.value = null
  imagePreviewFailed.value = false
}

function formatError(data, status) {
  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join('；') || `提交失败（HTTP ${status}）`
  }

  if (typeof data?.detail === 'string') return data.detail
  return `提交失败（HTTP ${status}），请稍后重试`
}

function buildPayload() {
  return {
    category: form.category,
    date: form.date,
    title: form.title.trim(),
    description: form.description,
    buttonText: form.buttonText,
    image: form.image,
    action: {
      type: form.actionType,
      target: form.actionType === 'none' ? '' : form.actionTarget,
    },
    sortOrder: Number.isInteger(form.sortOrder) ? form.sortOrder : 0,
    isActive: form.isActive ? 1 : 0,
  }
}

function formatUploadError(data, status) {
  if (typeof data?.detail === 'string') return data.detail
  return `图片上传失败（HTTP ${status}），请稍后重试`
}

function openImagePicker() {
  if (!isUploading.value && !isSubmitting.value) imageInput.value?.click()
}

async function uploadBannerImage(event) {
  const input = event.target
  const selectedFile = input.files?.[0]
  input.value = ''

  if (!selectedFile || isUploading.value) return

  uploadMessage.value = ''
  uploadError.value = ''
  imageOptimizationInfo.value = null

  if (!allowedImageTypes.has(selectedFile.type)) {
    uploadError.value = '请选择 JPG、PNG 或 WebP 图片'
    return
  }

  if (selectedFile.size > maxImageSize) {
    uploadError.value = '图片大小不能超过 5 MB'
    return
  }

  isUploading.value = true
  uploadStage.value = 'processing'

  try {
    const optimized = await optimizeBannerImage(selectedFile)
    imageOptimizationInfo.value = {
      originalSize: selectedFile.size,
      originalWidth: optimized.originalWidth,
      originalHeight: optimized.originalHeight,
      optimizedSize: optimized.file.size,
      optimizedWidth: optimized.optimizedWidth,
      optimizedHeight: optimized.optimizedHeight,
    }

    const formData = new FormData()
    formData.append('file', optimized.file)
    uploadStage.value = 'uploading'

    const response = await adminFetch(
      `${API_BASE_URL}/api/admin/uploads/banners`,
      {
        method: 'POST',
        body: formData,
      },
    )
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(formatUploadError(data, response.status))
    }

    if (typeof data?.url !== 'string' || !data.url) {
      throw new Error('图片上传成功，但服务器未返回图片地址')
    }

    form.image = data.url
    uploadMessage.value = '图片优化并上传成功'
  } catch (error) {
    uploadError.value = error instanceof Error
      ? error.message
      : '图片上传失败，请稍后重试'
  } finally {
    isUploading.value = false
    uploadStage.value = 'idle'
  }
}

async function loadBanner() {
  loading.value = true
  notFound.value = false
  loadError.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/banners/${encodeURIComponent(bannerId.value)}`,
    )

    if (response.status === 404) {
      notFound.value = true
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    const actionType = supportedActionTypes.has(data.action?.type)
      ? data.action.type
      : 'none'
    Object.assign(form, {
      category: data.category || '',
      date: data.date || '',
      title: data.title || '',
      description: data.description || '',
      buttonText: data.buttonText || '',
      image: data.image || '',
      actionType,
      actionTarget: actionType === 'none' ? '' : data.action?.target || '',
      sortOrder: Number(data.sortOrder) || 0,
      isActive: Number(data.isActive) === 1,
    })
  } catch (error) {
    console.error('Banner 加载失败：', error)
    loadError.value = 'Banner 加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function initializePage() {
  successMessage.value = ''
  errorMessage.value = ''
  createdId.value = null
  notFound.value = false
  loadError.value = ''
  uploadMessage.value = ''
  uploadError.value = ''
  uploadStage.value = 'idle'
  imageOptimizationInfo.value = null
  imagePreviewFailed.value = false

  if (isEdit.value) {
    await loadBanner()
  } else {
    loading.value = false
    resetForm()
  }
}

async function submitBanner() {
  if (
    isSubmitting.value
    || isUploading.value
    || (!isEdit.value && createdId.value !== null)
  ) return

  successMessage.value = ''
  errorMessage.value = ''

  if (!form.title.trim()) {
    errorMessage.value = '请输入 Banner 标题'
    return
  }

  isSubmitting.value = true

  try {
    const url = isEdit.value
      ? `${API_BASE_URL}/api/banners/${encodeURIComponent(bannerId.value)}`
      : `${API_BASE_URL}/api/banners`
    const response = await adminFetch(url, {
      method: isEdit.value ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildPayload()),
    })
    const data = await response.json().catch(() => null)

    if (response.status === 404 && isEdit.value) {
      notFound.value = true
      return
    }

    if (!response.ok) throw new Error(formatError(data, response.status))

    createdId.value = data.id
    successMessage.value = isEdit.value
      ? 'Banner 保存成功'
      : 'Banner 创建成功'
  } catch (error) {
    errorMessage.value = error instanceof Error
      ? error.message
      : '提交失败，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}

watch(() => route.fullPath, initializePage, { immediate: true })
watch(() => form.image, () => {
  imagePreviewFailed.value = false
})
</script>

<template>
  <main class="content-form-page">
    <div class="content-page-header">
      <div>
        <span>PORTAL CONTENT</span>
        <h1>{{ isEdit ? '编辑 Banner' : '新增 Banner' }}</h1>
        <p>维护轮播文案、动作和展示顺序。</p>
      </div>
    </div>

    <section v-if="loading" class="content-page-state" role="status">
      正在加载 Banner...
    </section>

    <section v-else-if="notFound" class="content-page-state">
      <h2>Banner 不存在</h2>
      <RouterLink to="/admin/content/banners">返回 Banner 管理</RouterLink>
    </section>

    <section
      v-else-if="loadError"
      class="content-page-state content-page-state-error"
      role="alert"
    >
      <h2>Banner 加载失败</h2>
      <p>{{ loadError }}</p>
      <RouterLink to="/admin/content/banners">返回 Banner 管理</RouterLink>
    </section>

    <form v-else class="content-form" @submit.prevent="submitBanner">
      <div class="content-form-grid">
        <label class="content-form-field content-form-field-wide">
          <span>标题 <strong aria-hidden="true">*</strong></span>
          <input
            v-model="form.title"
            type="text"
            required
            maxlength="200"
            placeholder="请输入 Banner 标题"
          >
        </label>

        <label class="content-form-field">
          <span>分类</span>
          <input
            v-model="form.category"
            type="text"
            maxlength="50"
            placeholder="例如：通知"
          >
        </label>

        <label class="content-form-field">
          <span>日期</span>
          <input v-model="form.date" type="date">
        </label>

        <label class="content-form-field content-form-field-wide">
          <span>描述</span>
          <textarea
            v-model="form.description"
            rows="4"
            maxlength="1000"
            placeholder="请输入 Banner 描述"
          />
        </label>

        <label class="content-form-field">
          <span>按钮文字</span>
          <input
            v-model="form.buttonText"
            type="text"
            maxlength="100"
            placeholder="例如：查看详情"
          >
        </label>

        <label class="content-form-field">
          <span>排序</span>
          <input v-model.number="form.sortOrder" type="number" min="0" step="1">
        </label>

        <div class="content-form-field content-form-field-wide banner-image-field">
          <span>Banner 图片</span>

          <div class="banner-upload-area">
            <div class="banner-upload-copy">
              <strong>{{ form.image ? '更换当前图片' : '上传 Banner 图片' }}</strong>
              <small>JPG / PNG / WebP，最大 5 MB</small>
              <small>上传后自动优化为 WebP，最大 1600 × 900</small>
            </div>

            <button
              type="button"
              class="banner-file-button"
              :disabled="isUploading || isSubmitting"
              @click="openImagePicker"
            >
              {{ uploadStage === 'processing'
                ? '处理中...'
                : uploadStage === 'uploading'
                  ? '上传中...'
                : form.image ? '重新选择图片' : '选择图片' }}
            </button>
            <input
              ref="imageInput"
              class="banner-file-input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              :disabled="isUploading || isSubmitting"
              @change="uploadBannerImage"
            >
          </div>

          <p
            v-if="imageOptimizationInfo"
            class="banner-optimization-info"
            role="status"
          >
            <span>
              原图：{{ formatFileSize(imageOptimizationInfo.originalSize) }} /
              {{ imageOptimizationInfo.originalWidth }}×{{ imageOptimizationInfo.originalHeight }}
            </span>
            <span aria-hidden="true">→</span>
            <span>
              优化后：{{ formatFileSize(imageOptimizationInfo.optimizedSize) }} /
              {{ imageOptimizationInfo.optimizedWidth }}×{{ imageOptimizationInfo.optimizedHeight }}
            </span>
          </p>

          <p v-if="uploadMessage" class="banner-upload-success" role="status">
            {{ uploadMessage }}
          </p>
          <p v-if="uploadError" class="banner-upload-error" role="alert">
            {{ uploadError }}
          </p>

          <div v-if="form.image" class="banner-image-current">
            <div
              v-if="imagePreviewUrl && !imagePreviewFailed"
              class="banner-image-preview"
            >
              <img
                :src="imagePreviewUrl"
                alt="当前 Banner 图片预览"
                @error="imagePreviewFailed = true"
              >
            </div>
            <p v-else class="banner-preview-unavailable">
              当前图片暂时无法预览
            </p>
            <p class="banner-image-path" :title="form.image">
              当前路径：<code>{{ form.image }}</code>
            </p>
          </div>

          <label class="banner-external-url">
            <span>或使用外部图片 URL</span>
            <input
              v-model="form.image"
              type="text"
              inputmode="url"
              maxlength="1000"
              placeholder="https://example.com/banner.jpg"
              :disabled="isUploading"
            >
          </label>
        </div>

        <label class="content-form-field">
          <span>动作类型</span>
          <select v-model="form.actionType">
            <option value="none">无动作</option>
            <option value="route">站内路由</option>
            <option value="external">外部链接</option>
          </select>
        </label>

        <label class="content-form-field">
          <span>动作目标</span>
          <input
            v-model="form.actionTarget"
            type="text"
            maxlength="1000"
            placeholder="例如：/news/1"
            :disabled="form.actionType === 'none'"
          >
        </label>
      </div>

      <label class="content-checkbox-field">
        <input v-model="form.isActive" type="checkbox">
        <span>
          <strong>启用 Banner</strong>
          <small>取消勾选后仅在管理列表中保留</small>
        </span>
      </label>

      <div
        v-if="successMessage"
        class="content-status-message content-status-success"
        role="status"
      >
        <strong>{{ successMessage }}</strong>
        <span>，ID：{{ createdId }}</span>
        <RouterLink
          v-if="!isEdit"
          :to="`/admin/content/banners/${createdId}/edit`"
        >
          继续编辑
        </RouterLink>
      </div>

      <div
        v-if="errorMessage"
        class="content-status-message content-status-error"
        role="alert"
      >
        {{ errorMessage }}
      </div>

      <div class="content-form-actions">
        <RouterLink to="/admin/content/banners">返回 Banner 管理</RouterLink>
        <button
          type="submit"
          :disabled="isSubmitting || isUploading || (!isEdit && createdId !== null)"
        >
          {{ isSubmitting
            ? '正在提交...'
            : isEdit ? '保存修改' : createdId ? '已创建' : '创建 Banner' }}
        </button>
      </div>
    </form>
  </main>
</template>

<style scoped>
.banner-image-field {
  gap: 12px;
}

.banner-upload-area {
  min-width: 0;
  padding: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface-soft);
}

.banner-upload-copy {
  min-width: 0;
  display: grid;
  gap: 5px;
}

.banner-upload-copy strong {
  color: var(--color-text);
  font-size: 14px;
}

.banner-upload-copy small,
.banner-external-url > span {
  color: var(--color-muted);
  font-size: 12px;
}

.banner-file-button {
  min-height: 38px;
  padding: 0 14px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(91, 91, 214, 0.3);
  border-radius: var(--radius-sm);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.banner-file-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.banner-file-input {
  display: none;
}

.banner-upload-success,
.banner-upload-error,
.banner-optimization-info,
.banner-preview-unavailable,
.banner-image-path {
  margin: 0;
  font-size: 13px;
}

.banner-upload-success {
  color: #36855a;
}

.banner-upload-error {
  color: #b45353;
}

.banner-optimization-info {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  color: var(--color-text-secondary);
}

.banner-image-current {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.banner-image-preview {
  width: 100%;
  max-height: 280px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #f8fafc;
}

.banner-image-preview img {
  display: block;
  max-width: 100%;
  max-height: 258px;
  object-fit: contain;
}

.banner-preview-unavailable,
.banner-image-path {
  color: var(--color-muted);
}

.banner-image-path {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.banner-image-path code {
  color: var(--color-text-secondary);
}

.banner-external-url {
  display: grid;
  gap: 7px;
}

@media (max-width: 600px) {
  .banner-upload-area {
    align-items: stretch;
    flex-direction: column;
  }

  .banner-file-button {
    width: 100%;
  }

  .banner-image-preview {
    max-height: 220px;
  }

  .banner-image-preview img {
    max-height: 198px;
  }
}
</style>
