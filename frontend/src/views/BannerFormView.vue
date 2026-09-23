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
      target: form.actionTarget,
    },
    sortOrder: Number.isInteger(form.sortOrder) ? form.sortOrder : 0,
    isActive: form.isActive ? 1 : 0,
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
    Object.assign(form, {
      category: data.category || '',
      date: data.date || '',
      title: data.title || '',
      description: data.description || '',
      buttonText: data.buttonText || '',
      image: data.image || '',
      actionType: data.action?.type || 'none',
      actionTarget: data.action?.target || '',
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

  if (isEdit.value) {
    await loadBanner()
  } else {
    loading.value = false
    resetForm()
  }
}

async function submitBanner() {
  if (isSubmitting.value || (!isEdit.value && createdId.value !== null)) return

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

        <label class="content-form-field content-form-field-wide">
          <span>图片路径或 URL</span>
          <input
            v-model="form.image"
            type="text"
            maxlength="1000"
            placeholder="/images/banners/example.jpg 或 https://..."
          >
        </label>

        <label class="content-form-field">
          <span>动作类型</span>
          <select v-model="form.actionType">
            <option value="none">无动作</option>
            <option value="route">站内路由</option>
            <option value="external">外部链接</option>
            <option value="dify">Dify 助手</option>
          </select>
        </label>

        <label class="content-form-field">
          <span>动作目标</span>
          <input
            v-model="form.actionTarget"
            type="text"
            maxlength="1000"
            placeholder="例如：/news/1"
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
          :disabled="isSubmitting || (!isEdit && createdId !== null)"
        >
          {{ isSubmitting
            ? '正在提交...'
            : isEdit ? '保存修改' : createdId ? '已创建' : '创建 Banner' }}
        </button>
      </div>
    </form>
  </main>
</template>
