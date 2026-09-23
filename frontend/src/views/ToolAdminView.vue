<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const tools = ref([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const deletingId = ref(null)
const togglingId = ref(null)

const statusLabels = {
  available: '可用',
  integrating: '待接入',
  developing: '开发中',
}

const actionLabels = {
  none: '无操作',
  route: '站内路由',
  static: '静态页面',
  external: '外部链接',
}

async function loadTools() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await adminFetch(`${API_BASE_URL}/api/admin/tools`)

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    tools.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('工具加载失败：', error)
    errorMessage.value = '工具加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function toggleActive(tool) {
  if (togglingId.value !== null) return

  const nextStatus = Number(tool.isActive) === 1 ? 0 : 1
  togglingId.value = tool.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/tools/${tool.id}/active`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isActive: nextStatus }),
      },
    )

    if (response.status === 404) {
      await loadTools()
      errorMessage.value = '工具不存在，列表已刷新'
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const updated = await response.json()
    tools.value = tools.value.map((item) =>
      item.id === updated.id
        ? { ...item, isActive: updated.isActive }
        : item,
    )
    successMessage.value = updated.isActive === 1
      ? '工具已启用'
      : '工具已停用'
  } catch (error) {
    console.error('工具状态更新失败：', error)
    errorMessage.value = '操作失败，请稍后重试'
  } finally {
    togglingId.value = null
  }
}

async function deleteTool(tool) {
  if (deletingId.value !== null) return
  if (!window.confirm('确定删除这个工具吗？删除后无法恢复。')) return

  deletingId.value = tool.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/tools/${tool.id}`,
      { method: 'DELETE' },
    )

    if (response.status === 404) {
      await loadTools()
      errorMessage.value = '工具不存在，列表已刷新'
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    tools.value = tools.value.filter((item) => item.id !== tool.id)
    successMessage.value = '工具删除成功'
  } catch (error) {
    console.error('工具删除失败：', error)
    errorMessage.value = '删除失败，请稍后重试'
  } finally {
    deletingId.value = null
  }
}

onMounted(loadTools)
</script>

<template>
  <main class="content-admin-page">
    <div class="content-page-header">
      <div>
        <span>PORTAL TOOLS</span>
        <h1>工具管理</h1>
        <p>维护 AI 与常用工具的状态、动作、顺序和启用状态。</p>
      </div>

      <RouterLink to="/admin/tools/new" class="content-primary-action">
        新增工具
      </RouterLink>
    </div>

    <div
      v-if="successMessage"
      class="content-status-message content-status-success"
      role="status"
    >
      {{ successMessage }}
    </div>

    <div
      v-if="errorMessage && !loading && tools.length"
      class="content-status-message content-status-error"
      role="alert"
    >
      {{ errorMessage }}
    </div>

    <section v-if="loading" class="content-page-state" role="status">
      正在加载工具...
    </section>

    <section
      v-else-if="errorMessage && !tools.length"
      class="content-page-state content-page-state-error"
      role="alert"
    >
      工具加载失败，请稍后重试
    </section>

    <section v-else-if="!tools.length" class="content-page-state">
      暂无工具
    </section>

    <div v-else class="content-table-card">
      <div class="content-table-scroll">
        <table class="content-table">
          <thead>
            <tr>
              <th>图标</th>
              <th>名称</th>
              <th>业务状态</th>
              <th>动作类型</th>
              <th>排序</th>
              <th>启用状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tool in tools" :key="tool.id">
              <td>
                <span class="tool-admin-icon">{{ tool.icon || '—' }}</span>
              </td>
              <td class="content-title-cell">
                <strong>{{ tool.title }}</strong>
                <small>{{ tool.description || '暂无描述' }}</small>
              </td>
              <td>{{ statusLabels[tool.status] || tool.status }}</td>
              <td>
                {{ actionLabels[tool.actionType] || tool.actionType }}
                <small v-if="tool.actionTarget" class="content-secondary">
                  {{ tool.actionTarget }}
                </small>
              </td>
              <td>{{ tool.sortOrder }}</td>
              <td>
                <span
                  class="content-state"
                  :class="{ 'is-active': Number(tool.isActive) === 1 }"
                >
                  {{ Number(tool.isActive) === 1 ? '已启用' : '已停用' }}
                </span>
              </td>
              <td>
                <div class="content-row-actions">
                  <RouterLink :to="`/admin/tools/${tool.id}/edit`">
                    编辑
                  </RouterLink>
                  <button
                    type="button"
                    class="status-action"
                    :disabled="togglingId !== null || deletingId !== null"
                    @click="toggleActive(tool)"
                  >
                    {{ togglingId === tool.id
                      ? '处理中...'
                      : Number(tool.isActive) === 1 ? '停用' : '启用' }}
                  </button>
                  <button
                    type="button"
                    class="delete-action"
                    :disabled="deletingId !== null || togglingId !== null"
                    @click="deleteTool(tool)"
                  >
                    {{ deletingId === tool.id ? '删除中...' : '删除' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>
</template>

<style scoped>
.tool-admin-icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-soft);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
}
</style>
