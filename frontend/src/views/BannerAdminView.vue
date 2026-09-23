<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const banners = ref([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const deletingId = ref(null)
const togglingId = ref(null)

async function loadBanners() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await adminFetch(`${API_BASE_URL}/api/admin/banners`)

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    banners.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Banner 加载失败：', error)
    errorMessage.value = 'Banner 加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function toggleActive(banner) {
  if (togglingId.value !== null) return

  const nextStatus = Number(banner.isActive) === 1 ? 0 : 1
  togglingId.value = banner.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/banners/${banner.id}/active`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isActive: nextStatus }),
      },
    )

    if (response.status === 404) {
      await loadBanners()
      errorMessage.value = 'Banner 不存在，列表已刷新'
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const updated = await response.json()
    banners.value = banners.value.map((item) =>
      item.id === updated.id
        ? { ...item, isActive: updated.isActive }
        : item,
    )
    successMessage.value = updated.isActive === 1
      ? 'Banner 已启用'
      : 'Banner 已停用'
  } catch (error) {
    console.error('Banner 状态更新失败：', error)
    errorMessage.value = '操作失败，请稍后重试'
  } finally {
    togglingId.value = null
  }
}

async function deleteBanner(banner) {
  if (deletingId.value !== null) return
  if (!window.confirm('确定删除这个 Banner 吗？删除后无法恢复。')) return

  deletingId.value = banner.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/banners/${banner.id}`,
      { method: 'DELETE' },
    )

    if (response.status === 404) {
      await loadBanners()
      errorMessage.value = 'Banner 不存在，列表已刷新'
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    banners.value = banners.value.filter((item) => item.id !== banner.id)
    successMessage.value = 'Banner 删除成功'
  } catch (error) {
    console.error('Banner 删除失败：', error)
    errorMessage.value = '删除失败，请稍后重试'
  } finally {
    deletingId.value = null
  }
}

onMounted(loadBanners)
</script>

<template>
  <main class="content-admin-page">
    <div class="content-page-header">
      <div>
        <span>PORTAL CONTENT</span>
        <h1>Banner 管理</h1>
        <p>维护门户轮播内容、顺序和启用状态。</p>
      </div>

      <RouterLink to="/admin/content/banners/new" class="content-primary-action">
        新增 Banner
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
      v-if="errorMessage && !loading && banners.length"
      class="content-status-message content-status-error"
      role="alert"
    >
      {{ errorMessage }}
    </div>

    <section v-if="loading" class="content-page-state" role="status">
      正在加载 Banner...
    </section>

    <section
      v-else-if="errorMessage && !banners.length"
      class="content-page-state content-page-state-error"
      role="alert"
    >
      Banner 加载失败，请稍后重试
    </section>

    <section v-else-if="!banners.length" class="content-page-state">
      暂无 Banner
    </section>

    <div v-else class="content-table-card">
      <div class="content-table-scroll">
        <table class="content-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>分类</th>
              <th>日期</th>
              <th>动作</th>
              <th>排序</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="banner in banners" :key="banner.id">
              <td class="content-title-cell">
                <strong>{{ banner.title }}</strong>
                <small>{{ banner.description || '暂无描述' }}</small>
              </td>
              <td>{{ banner.category || '—' }}</td>
              <td>{{ banner.date || '—' }}</td>
              <td>
                {{ banner.action?.type || 'none' }}
                <small v-if="banner.action?.target" class="content-secondary">
                  {{ banner.action.target }}
                </small>
              </td>
              <td>{{ banner.sortOrder }}</td>
              <td>
                <span
                  class="content-state"
                  :class="{ 'is-active': Number(banner.isActive) === 1 }"
                >
                  {{ Number(banner.isActive) === 1 ? '已启用' : '已停用' }}
                </span>
              </td>
              <td>
                <div class="content-row-actions">
                  <RouterLink :to="`/admin/content/banners/${banner.id}/edit`">
                    编辑
                  </RouterLink>
                  <button
                    type="button"
                    class="status-action"
                    :disabled="togglingId !== null || deletingId !== null"
                    @click="toggleActive(banner)"
                  >
                    {{ togglingId === banner.id
                      ? '处理中...'
                      : Number(banner.isActive) === 1 ? '停用' : '启用' }}
                  </button>
                  <button
                    type="button"
                    class="delete-action"
                    :disabled="deletingId !== null || togglingId !== null"
                    @click="deleteBanner(banner)"
                  >
                    {{ deletingId === banner.id ? '删除中...' : '删除' }}
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
