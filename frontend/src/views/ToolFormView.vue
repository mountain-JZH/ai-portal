<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const route = useRoute()
const isEdit = computed(() => Boolean(route.params.id))
const toolId = computed(() => String(route.params.id || ''))

const form = reactive({
  icon: '',
  title: '',
  description: '',
  status: 'available',
  actionType: 'none',
  actionTarget: '',
  buttonText: '',
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

const actionTargetHint = computed(() => {
  const hints = {
    none: '无操作不需要目标地址',
    route: '填写 Vue 站内路由，例如 /tools',
    static: '填写静态页面路径，例如 /tools/qstart/index.html',
    external: '填写由用户浏览器直接访问的 URL 或公司内网地址',
  }

  return hints[form.actionType]
})

const actionTargetPlaceholder = computed(() => {
  if (form.actionType === 'route') return '/tools'
  if (form.actionType === 'static') return '/tools/qstart/index.html'
  if (form.actionType === 'external') return '请输入目标地址'
  return '无需填写'
})

function resetForm() {
  Object.assign(form, {
    icon: '',
    title: '',
    description: '',
    status: 'available',
    actionType: 'none',
    actionTarget: '',
    buttonText: '',
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
    icon: form.icon,
    title: form.title.trim(),
    description: form.description,
    status: form.status,
    actionType: form.actionType,
    actionTarget: form.actionType === 'none' ? '' : form.actionTarget,
    buttonText: form.buttonText,
    sortOrder: Number.isInteger(form.sortOrder) ? form.sortOrder : 0,
    isActive: form.isActive ? 1 : 0,
  }
}

async function loadTool() {
  loading.value = true
  notFound.value = false
  loadError.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/tools/${encodeURIComponent(toolId.value)}`,
    )

    if (response.status === 404) {
      notFound.value = true
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    Object.assign(form, {
      icon: data.icon || '',
      title: data.title || '',
      description: data.description || '',
      status: data.status || 'developing',
      actionType: data.actionType || 'none',
      actionTarget: data.actionTarget || '',
      buttonText: data.buttonText || '',
      sortOrder: Number(data.sortOrder) || 0,
      isActive: Number(data.isActive) === 1,
    })
  } catch (error) {
    console.error('工具加载失败：', error)
    loadError.value = '工具加载失败，请稍后重试'
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
    await loadTool()
  } else {
    loading.value = false
    resetForm()
  }
}

async function submitTool() {
  if (isSubmitting.value || (!isEdit.value && createdId.value !== null)) return

  successMessage.value = ''
  errorMessage.value = ''

  if (!form.title.trim()) {
    errorMessage.value = '请输入工具名称'
    return
  }

  isSubmitting.value = true

  try {
    const url = isEdit.value
      ? `${API_BASE_URL}/api/tools/${encodeURIComponent(toolId.value)}`
      : `${API_BASE_URL}/api/tools`
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
      ? '工具保存成功'
      : '工具创建成功'
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
        <span>PORTAL TOOLS</span>
        <h1>{{ isEdit ? '编辑工具' : '新增工具' }}</h1>
        <p>维护工具展示信息、业务状态、动作和排序。</p>
      </div>
    </div>

    <section v-if="loading" class="content-page-state" role="status">
      正在加载工具...
    </section>

    <section v-else-if="notFound" class="content-page-state">
      <h2>工具不存在</h2>
      <RouterLink to="/admin/tools">返回工具管理</RouterLink>
    </section>

    <section
      v-else-if="loadError"
      class="content-page-state content-page-state-error"
      role="alert"
    >
      <h2>工具加载失败</h2>
      <p>{{ loadError }}</p>
      <RouterLink to="/admin/tools">返回工具管理</RouterLink>
    </section>

    <form v-else class="content-form" @submit.prevent="submitTool">
      <div class="content-form-grid">
        <label class="content-form-field">
          <span>图标</span>
          <input
            v-model="form.icon"
            type="text"
            maxlength="50"
            placeholder="例如：KB"
          >
          <small class="tool-form-hint">当前使用简短文本或字符作为图标。</small>
        </label>

        <label class="content-form-field">
          <span>名称 <strong aria-hidden="true">*</strong></span>
          <input
            v-model="form.title"
            type="text"
            required
            maxlength="200"
            placeholder="请输入工具名称"
          >
        </label>

        <label class="content-form-field content-form-field-wide">
          <span>描述</span>
          <textarea
            v-model="form.description"
            rows="4"
            maxlength="1000"
            placeholder="请输入工具描述"
          />
        </label>

        <label class="content-form-field">
          <span>业务状态</span>
          <select v-model="form.status">
            <option value="available">可用</option>
            <option value="integrating">待接入</option>
            <option value="developing">开发中</option>
          </select>
        </label>

        <label class="content-form-field">
          <span>按钮文字</span>
          <input
            v-model="form.buttonText"
            type="text"
            maxlength="100"
            placeholder="例如：立即使用"
          >
        </label>

        <label class="content-form-field">
          <span>动作类型</span>
          <select v-model="form.actionType">
            <option value="none">无操作</option>
            <option value="route">站内路由</option>
            <option value="static">静态页面</option>
            <option value="external">外部链接</option>
          </select>
        </label>

        <label class="content-form-field">
          <span>排序</span>
          <input v-model.number="form.sortOrder" type="number" min="0" step="1">
        </label>

        <label class="content-form-field content-form-field-wide">
          <span>动作目标</span>
          <input
            v-model="form.actionTarget"
            type="text"
            maxlength="1000"
            :disabled="form.actionType === 'none'"
            :placeholder="actionTargetPlaceholder"
            aria-describedby="tool-action-target-hint"
          >
          <small id="tool-action-target-hint" class="tool-form-hint">
            {{ actionTargetHint }}
          </small>
        </label>
      </div>

      <label class="content-checkbox-field">
        <input v-model="form.isActive" type="checkbox">
        <span>
          <strong>启用工具</strong>
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
          :to="`/admin/tools/${createdId}/edit`"
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
        <RouterLink to="/admin/tools">返回工具管理</RouterLink>
        <button
          type="submit"
          :disabled="isSubmitting || (!isEdit && createdId !== null)"
        >
          {{ isSubmitting
            ? '正在提交...'
            : isEdit ? '保存修改' : createdId ? '已创建' : '创建工具' }}
        </button>
      </div>
    </form>
  </main>
</template>

<style scoped>
.tool-form-hint {
  color: var(--color-muted);
  font-size: 12px;
  line-height: 1.5;
}

.content-form-field input:disabled {
  background: var(--color-surface-soft);
  color: var(--color-muted);
  cursor: not-allowed;
}
</style>
