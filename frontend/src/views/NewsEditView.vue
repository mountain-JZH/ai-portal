<script setup>
import {
  computed,
  reactive,
  ref,
  watch,
} from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { API_BASE_URL } from '../config/api'

const route = useRoute()
const newsId = computed(() => String(route.params.id))

const form = reactive({
  title: '',
  summary: '',
  source_type: '内部动态',
  source: '',
  publish_date: '',
  keywords: '',
  url: '',
  content: '',
  is_published: true,
})

const loading = ref(true)
const notFound = ref(false)
const loadError = ref('')
const isSaving = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const savedNewsId = ref(null)

function formatError(data, status) {
  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join('；') || `保存失败（HTTP ${status}）`
  }

  if (typeof data?.detail === 'string') {
    return data.detail
  }

  return `保存失败（HTTP ${status}），请稍后重试`
}

async function loadNews(id) {
  loading.value = true
  notFound.value = false
  loadError.value = ''
  successMessage.value = ''
  errorMessage.value = ''
  savedNewsId.value = null

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/news/${encodeURIComponent(id)}`,
    )

    if (response.status === 404) {
      notFound.value = true
      return
    }

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    const data = await response.json()

    form.title = data.title
    form.summary = data.summary
    form.content = data.content
    form.source = data.source
    form.source_type = data.source_type
    form.publish_date = data.publish_date
    form.keywords = data.keywords
    form.url = data.url
    form.is_published = data.is_published === 1
  } catch (error) {
    console.error('新闻加载失败：', error)
    loadError.value = '新闻加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function saveNews() {
  if (isSaving.value) return

  successMessage.value = ''
  errorMessage.value = ''
  savedNewsId.value = null

  if (!form.title.trim()) {
    errorMessage.value = '请输入新闻标题'
    return
  }

  isSaving.value = true

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/news/${encodeURIComponent(newsId.value)}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: form.title.trim(),
          summary: form.summary,
          content: form.content,
          source: form.source,
          source_type: form.source_type,
          publish_date: form.publish_date,
          keywords: form.keywords,
          url: form.url,
          is_published: form.is_published ? 1 : 0,
        }),
      },
    )

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(formatError(data, response.status))
    }

    savedNewsId.value = data.id
    successMessage.value = '新闻修改成功'
  } catch (error) {
    errorMessage.value = error instanceof Error
      ? error.message
      : '保存失败，请稍后重试'
  } finally {
    isSaving.value = false
  }
}

watch(newsId, (id) => loadNews(id), { immediate: true })
</script>

<template>
  <main class="page">
    <div class="page-header">
      <span>NEWS MANAGEMENT</span>
      <h1>编辑新闻</h1>
      <p>修改新闻内容并保存到门户数据库。</p>
    </div>

    <section
      v-if="loading"
      class="page-state"
      role="status"
    >
      正在加载新闻...
    </section>

    <section
      v-else-if="notFound"
      class="page-state"
    >
      <h2>新闻不存在</h2>
      <RouterLink to="/admin/news">返回新闻管理</RouterLink>
    </section>

    <section
      v-else-if="loadError"
      class="page-state page-state-error"
      role="alert"
    >
      <h2>新闻加载失败</h2>
      <p>{{ loadError }}</p>
      <RouterLink to="/admin/news">返回新闻管理</RouterLink>
    </section>

    <form
      v-else
      class="news-form"
      @submit.prevent="saveNews"
    >
      <div class="form-grid">
        <label class="form-field form-field-wide">
          <span>标题 <strong aria-hidden="true">*</strong></span>
          <input
            v-model="form.title"
            type="text"
            required
            maxlength="200"
            placeholder="请输入新闻标题"
          >
        </label>

        <label class="form-field form-field-wide">
          <span>摘要</span>
          <textarea
            v-model="form.summary"
            rows="3"
            placeholder="请输入新闻摘要"
          />
        </label>

        <label class="form-field">
          <span>新闻类型</span>
          <select v-model="form.source_type">
            <option value="内部动态">内部动态</option>
            <option value="行业资讯">行业资讯</option>
            <option value="AI资讯">AI资讯</option>
            <option value="通知公告">通知公告</option>
          </select>
        </label>

        <label class="form-field">
          <span>来源</span>
          <input
            v-model="form.source"
            type="text"
            placeholder="请输入新闻来源"
          >
        </label>

        <label class="form-field">
          <span>发布日期</span>
          <input
            v-model="form.publish_date"
            type="date"
          >
        </label>

        <label class="form-field">
          <span>关键词</span>
          <input
            v-model="form.keywords"
            type="text"
            placeholder="多个关键词用英文逗号分隔"
          >
        </label>

        <label class="form-field form-field-wide">
          <span>原文链接</span>
          <input
            v-model="form.url"
            type="url"
            placeholder="https://example.com/news"
          >
        </label>

        <label class="form-field form-field-wide">
          <span>正文</span>
          <textarea
            v-model="form.content"
            rows="10"
            placeholder="请输入新闻正文"
          />
        </label>
      </div>

      <label class="publish-field">
        <input
          v-model="form.is_published"
          type="checkbox"
        >
        <span>
          <strong>立即发布</strong>
          <small>取消勾选后将以未发布状态保存</small>
        </span>
      </label>

      <div
        v-if="successMessage"
        class="status-message status-success"
        role="status"
      >
        <strong>{{ successMessage }}</strong>
        <span>新闻 ID：{{ savedNewsId }}</span>
      </div>

      <div
        v-if="errorMessage"
        class="status-message status-error"
        role="alert"
      >
        {{ errorMessage }}
      </div>

      <div class="form-actions">
        <RouterLink to="/admin/news">返回新闻管理</RouterLink>
        <RouterLink :to="`/news/${newsId}`">查看新闻</RouterLink>

        <button
          type="submit"
          :disabled="isSaving"
        >
          {{ isSaving ? '正在保存...' : '保存修改' }}
        </button>
      </div>
    </form>
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

.news-form,
.page-state {
  max-width: 900px;
  padding: 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.page-state {
  color: var(--color-text-secondary);
  text-align: center;
}

.page-state h2 {
  margin: 0 0 12px;
  color: var(--color-text);
}

.page-state p {
  margin: 0 0 18px;
}

.page-state a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

.page-state-error h2,
.page-state-error p {
  color: #9b4545;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.form-field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.form-field-wide {
  grid-column: 1 / -1;
}

.form-field > span {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
}

.form-field strong {
  color: #b45353;
}

.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.form-field input,
.form-field select {
  height: 44px;
  padding: 0 13px;
}

.form-field textarea {
  min-height: 92px;
  padding: 11px 13px;
  resize: vertical;
  line-height: 1.7;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  border-color: var(--color-primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.12);
}

.form-field input::placeholder,
.form-field textarea::placeholder {
  color: var(--color-muted);
}

.publish-field {
  margin-top: 26px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-soft);
  cursor: pointer;
}

.publish-field input {
  width: 17px;
  height: 17px;
  margin: 2px 0 0;
  accent-color: var(--color-primary);
}

.publish-field span {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.publish-field strong {
  color: var(--color-text);
  font-size: 14px;
}

.publish-field small {
  color: var(--color-muted);
  font-size: 12px;
}

.status-message {
  margin-top: 20px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
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

.form-actions {
  margin-top: 28px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
}

.form-actions a {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;
}

.form-actions a:hover {
  color: var(--color-primary);
}

.form-actions button {
  min-width: 120px;
  height: 44px;
  padding: 0 22px;
  border: 0;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: white;
  cursor: pointer;
  font-weight: 600;
  box-shadow: 0 6px 16px rgba(91, 91, 214, 0.18);
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast);
}

.form-actions button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.form-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

@media (max-width: 767px) {
  .page {
    width: calc(100% - 32px);
    padding: 40px 0 72px;
  }

  .page-header {
    margin-bottom: 28px;
  }

  .page-header h1 {
    font-size: 32px;
  }

  .news-form,
  .page-state {
    padding: 22px 18px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .form-field-wide {
    grid-column: auto;
  }

  .status-message,
  .form-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .form-actions button {
    width: 100%;
  }
}
</style>
