<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const announcements = ref([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const deletingId = ref(null)
const togglingId = ref(null)

async function loadAnnouncements() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await adminFetch(`${API_BASE_URL}/api/admin/announcements`)

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    announcements.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('平台公告加载失败：', error)
    errorMessage.value = '平台公告加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function toggleActive(announcement) {
  if (togglingId.value !== null) return

  const nextStatus = Number(announcement.isActive) === 1 ? 0 : 1
  togglingId.value = announcement.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/announcements/${announcement.id}/active`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isActive: nextStatus }),
      },
    )

    if (response.status === 404) {
      await loadAnnouncements()
      errorMessage.value = '公告不存在，列表已刷新'
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const updated = await response.json()
    announcements.value = announcements.value.map((item) =>
      item.id === updated.id
        ? { ...item, isActive: updated.isActive }
        : item,
    )
    successMessage.value = updated.isActive === 1
      ? '公告已启用'
      : '公告已停用'
  } catch (error) {
    console.error('公告状态更新失败：', error)
    errorMessage.value = '操作失败，请稍后重试'
  } finally {
    togglingId.value = null
  }
}

async function deleteAnnouncement(announcement) {
  if (deletingId.value !== null) return
  if (!window.confirm('确定删除这条公告吗？删除后无法恢复。')) return

  deletingId.value = announcement.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/announcements/${announcement.id}`,
      { method: 'DELETE' },
    )

    if (response.status === 404) {
      await loadAnnouncements()
      errorMessage.value = '公告不存在，列表已刷新'
      return
    }

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    announcements.value = announcements.value.filter(
      (item) => item.id !== announcement.id,
    )
    successMessage.value = '公告删除成功'
  } catch (error) {
    console.error('公告删除失败：', error)
    errorMessage.value = '删除失败，请稍后重试'
  } finally {
    deletingId.value = null
  }
}

onMounted(loadAnnouncements)
</script>

<template>
  <main class="content-admin-page">
    <div class="content-page-header">
      <div>
        <span>PORTAL CONTENT</span>
        <h1>平台公告</h1>
        <p>维护门户顶部公告内容、顺序和启用状态。</p>
      </div>

      <RouterLink
        to="/admin/content/announcements/new"
        class="content-primary-action"
      >
        新增公告
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
      v-if="errorMessage && !loading && announcements.length"
      class="content-status-message content-status-error"
      role="alert"
    >
      {{ errorMessage }}
    </div>

    <section v-if="loading" class="content-page-state" role="status">
      正在加载公告...
    </section>

    <section
      v-else-if="errorMessage && !announcements.length"
      class="content-page-state content-page-state-error"
      role="alert"
    >
      平台公告加载失败，请稍后重试
    </section>

    <section v-else-if="!announcements.length" class="content-page-state">
      暂无公告
    </section>

    <div v-else class="content-table-card">
      <div class="content-table-scroll">
        <table class="content-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>日期</th>
              <th>排序</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="announcement in announcements" :key="announcement.id">
              <td class="content-title-cell">
                <strong>{{ announcement.title }}</strong>
                <small>{{ announcement.summary || '暂无摘要' }}</small>
              </td>
              <td>{{ announcement.date || '—' }}</td>
              <td>{{ announcement.sortOrder }}</td>
              <td>
                <span
                  class="content-state"
                  :class="{ 'is-active': Number(announcement.isActive) === 1 }"
                >
                  {{ Number(announcement.isActive) === 1 ? '已启用' : '已停用' }}
                </span>
              </td>
              <td>
                <div class="content-row-actions">
                  <RouterLink
                    :to="`/admin/content/announcements/${announcement.id}/edit`"
                  >
                    编辑
                  </RouterLink>
                  <button
                    type="button"
                    class="status-action"
                    :disabled="togglingId !== null || deletingId !== null"
                    @click="toggleActive(announcement)"
                  >
                    {{ togglingId === announcement.id
                      ? '处理中...'
                      : Number(announcement.isActive) === 1 ? '停用' : '启用' }}
                  </button>
                  <button
                    type="button"
                    class="delete-action"
                    :disabled="deletingId !== null || togglingId !== null"
                    @click="deleteAnnouncement(announcement)"
                  >
                    {{ deletingId === announcement.id ? '删除中...' : '删除' }}
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
