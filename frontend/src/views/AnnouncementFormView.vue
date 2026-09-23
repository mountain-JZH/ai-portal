<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const route = useRoute()
const isEdit = computed(() => Boolean(route.params.id))
const announcementId = computed(() => String(route.params.id || ''))

function getLocalDateKey() {
  const now = new Date()
  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-')
}

const form = reactive({
  title: '',
  summary: '',
  date: getLocalDateKey(),
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
    title: '',
    summary: '',
    date: getLocalDateKey(),
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
    title: form.title.trim(),
    summary: form.summary,
    date: form.date,
    sortOrder: Number.isInteger(form.sortOrder) ? form.sortOrder : 0,
    isActive: form.isActive ? 1 : 0,
  }
}

async function loadAnnouncement() {
  loading.value = true
  notFound.value = false
  loadError.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/announcements/${encodeURIComponent(announcementId.value)}`,
    )

    if (response.status === 404) {
      notFound.value = true
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    Object.assign(form, {
      title: data.title || '',
      summary: data.summary || '',
      date: data.date || '',
      sortOrder: Number(data.sortOrder) || 0,
      isActive: Number(data.isActive) === 1,
    })
  } catch (error) {
    console.error('平台公告加载失败：', error)
    loadError.value = '平台公告加载失败，请稍后重试'
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
    await loadAnnouncement()
  } else {
    loading.value = false
    resetForm()
  }
}

async function submitAnnouncement() {
  if (isSubmitting.value || (!isEdit.value && createdId.value !== null)) return

  successMessage.value = ''
  errorMessage.value = ''

  if (!form.title.trim()) {
    errorMessage.value = '请输入公告标题'
    return
  }

  isSubmitting.value = true

  try {
    const url = isEdit.value
      ? `${API_BASE_URL}/api/announcements/${encodeURIComponent(announcementId.value)}`
      : `${API_BASE_URL}/api/announcements`
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
      ? '公告保存成功'
      : '公告创建成功'
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
        <h1>{{ isEdit ? '编辑公告' : '新增公告' }}</h1>
        <p>维护平台公告文案、日期和展示顺序。</p>
      </div>
    </div>

    <section v-if="loading" class="content-page-state" role="status">
      正在加载公告...
    </section>

    <section v-else-if="notFound" class="content-page-state">
      <h2>公告不存在</h2>
      <RouterLink to="/admin/content/announcements">返回公告管理</RouterLink>
    </section>

    <section
      v-else-if="loadError"
      class="content-page-state content-page-state-error"
      role="alert"
    >
      <h2>公告加载失败</h2>
      <p>{{ loadError }}</p>
      <RouterLink to="/admin/content/announcements">返回公告管理</RouterLink>
    </section>

    <form v-else class="content-form" @submit.prevent="submitAnnouncement">
      <div class="content-form-grid">
        <label class="content-form-field content-form-field-wide">
          <span>标题 <strong aria-hidden="true">*</strong></span>
          <input
            v-model="form.title"
            type="text"
            required
            maxlength="200"
            placeholder="请输入公告标题"
          >
        </label>

        <label class="content-form-field content-form-field-wide">
          <span>摘要</span>
          <textarea
            v-model="form.summary"
            rows="5"
            maxlength="1000"
            placeholder="请输入公告摘要"
          />
        </label>

        <label class="content-form-field">
          <span>日期</span>
          <input v-model="form.date" type="date">
        </label>

        <label class="content-form-field">
          <span>排序</span>
          <input v-model.number="form.sortOrder" type="number" min="0" step="1">
        </label>
      </div>

      <label class="content-checkbox-field">
        <input v-model="form.isActive" type="checkbox">
        <span>
          <strong>启用公告</strong>
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
          :to="`/admin/content/announcements/${createdId}/edit`"
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
        <RouterLink to="/admin/content/announcements">返回公告管理</RouterLink>
        <button
          type="submit"
          :disabled="isSubmitting || (!isEdit && createdId !== null)"
        >
          {{ isSubmitting
            ? '正在提交...'
            : isEdit ? '保存修改' : createdId ? '已创建' : '创建公告' }}
        </button>
      </div>
    </form>
  </main>
</template>
