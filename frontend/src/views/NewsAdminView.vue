<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const newsList = ref([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const deletingId = ref(null)
const publishingId = ref(null)

async function loadNews() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await adminFetch(`${API_BASE_URL}/api/admin/news`)

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    newsList.value = await response.json()
  } catch (error) {
    console.error('新闻加载失败：', error)
    errorMessage.value = '新闻加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function deleteNews(news) {
  if (deletingId.value !== null) return

  const confirmed = window.confirm(
    '确定删除这条新闻吗？删除后无法恢复。',
  )

  if (!confirmed) return

  deletingId.value = news.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/news/${news.id}`,
      { method: 'DELETE' },
    )

    if (response.status === 404) {
      await loadNews()
      errorMessage.value = '新闻不存在，列表已刷新'
      return
    }

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    newsList.value = newsList.value.filter(
      (item) => item.id !== news.id,
    )
    successMessage.value = '新闻删除成功'
  } catch (error) {
    console.error('新闻删除失败：', error)
    errorMessage.value = '删除失败，请稍后重试'
  } finally {
    deletingId.value = null
  }
}

async function togglePublishStatus(news) {
  if (publishingId.value !== null) return

  const nextStatus = news.is_published === 1 ? 0 : 1
  publishingId.value = news.id
  successMessage.value = ''
  errorMessage.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE_URL}/api/news/${news.id}/publish`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_published: nextStatus }),
      },
    )

    if (response.status === 404) {
      await loadNews()
      errorMessage.value = '新闻不存在，列表已刷新'
      return
    }

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    const updatedNews = await response.json()
    const currentNews = newsList.value.find(
      (item) => item.id === updatedNews.id,
    )

    if (currentNews) {
      currentNews.is_published = updatedNews.is_published
    }

    successMessage.value = updatedNews.is_published === 1
      ? '新闻已发布'
      : '新闻已下架'
  } catch (error) {
    console.error('新闻发布状态更新失败：', error)
    errorMessage.value = '操作失败，请稍后重试'
  } finally {
    publishingId.value = null
  }
}

onMounted(() => {
  loadNews()
})
</script>

<template>
  <main class="page">
    <div class="page-header">
      <div>
        <span>NEWS MANAGEMENT</span>
        <h1>新闻管理</h1>
        <p>查看并维护门户中的新闻内容。</p>
      </div>

      <RouterLink
        to="/admin/news/new"
        class="primary-action"
      >
        新增新闻
      </RouterLink>
    </div>

    <div
      v-if="successMessage"
      class="status-message status-success"
      role="status"
    >
      {{ successMessage }}
    </div>

    <div
      v-if="errorMessage && !loading && newsList.length"
      class="status-message status-error"
      role="alert"
    >
      {{ errorMessage }}
    </div>

    <section
      v-if="loading"
      class="page-state"
      role="status"
    >
      正在加载新闻...
    </section>

    <section
      v-else-if="errorMessage && !newsList.length"
      class="page-state page-state-error"
    >
      新闻加载失败，请稍后重试
    </section>

    <section
      v-else-if="!newsList.length"
      class="page-state"
    >
      暂无新闻
    </section>

    <div
      v-else
      class="table-card"
    >
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>标题</th>
              <th>新闻类型</th>
              <th>发布日期</th>
              <th>来源</th>
              <th>发布状态</th>
              <th>操作</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="news in newsList"
              :key="news.id"
            >
              <td>
                <RouterLink
                  :to="`/news/${news.id}`"
                  class="news-title"
                >
                  {{ news.title }}
                </RouterLink>
              </td>
              <td>{{ news.source_type || '—' }}</td>
              <td>{{ news.publish_date || '—' }}</td>
              <td>{{ news.source || '—' }}</td>
              <td>
                <span
                  class="publish-status"
                  :class="{
                    'is-published': news.is_published === 1,
                  }"
                >
                  {{ news.is_published === 1 ? '已发布' : '未发布' }}
                </span>
              </td>
              <td>
                <div class="row-actions">
                  <RouterLink :to="`/admin/news/${news.id}/edit`">
                    编辑
                  </RouterLink>
                  <button
                    type="button"
                    class="publish-action"
                    :disabled="publishingId !== null"
                    @click="togglePublishStatus(news)"
                  >
                    {{ publishingId === news.id
                      ? '处理中...'
                      : news.is_published === 1 ? '下架' : '发布' }}
                  </button>
                  <button
                    type="button"
                    :disabled="deletingId !== null"
                    @click="deleteNews(news)"
                  >
                    {{ deletingId === news.id ? '删除中...' : '删除' }}
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
.page {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 0 auto;
  padding: 56px 0 96px;
}

.page-header {
  position: relative;
  margin-bottom: 38px;
  padding-bottom: 20px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.page-header::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 42px;
  height: 3px;
  border-radius: 2px;
  background: var(--color-primary);
}

.page-header span {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
}

.page-header h1 {
  margin: 12px 0 10px;
  color: var(--color-text);
  font-size: 40px;
  line-height: 1.25;
}

.page-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.primary-action {
  flex-shrink: 0;
  padding: 11px 20px;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: white;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 6px 16px rgba(91, 91, 214, 0.18);
}

.table-card,
.page-state {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.table-card {
  overflow: hidden;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 850px;
  border-collapse: collapse;
}

th,
td {
  padding: 17px 18px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 14px;
  text-align: left;
  vertical-align: middle;
}

th {
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 600;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover {
  background: var(--color-surface-soft);
}

.news-title {
  color: var(--color-text);
  text-decoration: none;
  font-weight: 600;
}

.news-title:hover,
.row-actions a:hover {
  color: var(--color-primary);
}

.publish-status {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: var(--radius-xs);
  background: #f1f3f6;
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 600;
}

.publish-status.is-published {
  background: #eaf5f0;
  color: #3f765f;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.row-actions a,
.row-actions button {
  color: var(--color-text-secondary);
  font-size: 13px;
  text-decoration: none;
}

.row-actions button {
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.row-actions button:hover:not(:disabled) {
  color: #b45353;
}

.row-actions .publish-action:hover:not(:disabled) {
  color: var(--color-primary);
}

.row-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.status-message {
  margin-bottom: 18px;
  padding: 13px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
}

.status-success {
  border: 1px solid #cfe8dc;
  background: #eff8f4;
  color: #356b55;
}

.status-error {
  border: 1px solid #ecd1d1;
  background: #fcf3f3;
  color: #9b4545;
}

.page-state {
  padding: 72px 24px;
  color: var(--color-muted);
  text-align: center;
}

.page-state-error {
  color: #b45353;
}

@media (max-width: 767px) {
  .page {
    width: calc(100% - 32px);
    padding: 40px 0 72px;
  }

  .page-header {
    margin-bottom: 28px;
    align-items: flex-start;
    flex-direction: column;
  }

  .page-header h1 {
    font-size: 32px;
  }

  .primary-action {
    width: 100%;
    text-align: center;
  }

  th,
  td {
    padding: 14px;
  }
}
</style>
