<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'

const latestNews = ref([])
const loading = ref(true)
const errorMessage = ref('')

async function loadNews() {
  try {
    loading.value = true
    errorMessage.value = ''

    const response = await fetch(`${API_BASE_URL}/api/news`)

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    const data = await response.json()

    latestNews.value = data
      .map((news) => ({
        ...news,

        // 后端字段转换为当前前端使用的字段
        type: news.source_type,
        date: news.publish_date,
      }))
      .sort((first, second) =>
        String(second.date).localeCompare(String(first.date)),
      )
      .slice(0, 3)

  } catch (error) {
    console.error('新闻加载失败：', error)

    errorMessage.value = '新闻加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadNews()
})
</script>

<template>
  <section class="section">
    <div class="section-header">
      <div>
        <h2>最新动态</h2>
        <p>关注内部通知、信息宣贯及行业动态</p>
      </div>

      <RouterLink to="/news">
        查看全部 →
      </RouterLink>
    </div>

    <!-- 加载中 -->
    <div
      v-if="loading"
      class="status-message"
    >
      正在加载最新动态...
    </div>

    <!-- 加载失败 -->
    <div
      v-else-if="errorMessage"
      class="status-message error-message"
    >
      {{ errorMessage }}
    </div>

    <!-- 没有新闻 -->
    <div
      v-else-if="latestNews.length === 0"
      class="status-message"
    >
      暂无新闻
    </div>

    <!-- 正常新闻列表 -->
    <div
      v-else
      class="news-list"
    >
      <RouterLink
        v-for="news in latestNews"
        :key="news.id"
        :to="`/news/${news.id}`"
        class="news-item"
      >
        <div class="news-content">
          <div class="news-main">
            <span class="news-type">
              {{ news.type }}
            </span>

            <span class="news-title">
              {{ news.title }}
            </span>
          </div>

          <p class="news-summary">
            {{ news.summary }}
          </p>
        </div>

        <time
          class="news-date"
          :datetime="news.date"
        >
          {{ news.date }}
        </time>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.section {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 72px auto;
  padding: 22px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}

.section-header {
  margin-bottom: 24px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.section-header h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.3;
  color: var(--color-text);
}

.section-header p {
  margin: 8px 0 0;
  color: var(--color-muted);
  font-size: 14px;
}

.section-header a {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: color var(--transition-fast);
}

.section-header a:hover {
  color: var(--color-primary);
}

.status-message {
  padding: 28px 12px;
  border-top: 1px solid var(--color-border);
  color: var(--color-muted);
  font-size: 14px;
  text-align: center;
}

.error-message {
  color: #b45353;
}

.news-list {
  border-top: 1px solid var(--color-border);
}

.news-item {
  min-height: 104px;
  padding: 16px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border-bottom: 1px solid var(--color-border);
  color: inherit;
  text-decoration: none;
  transition:
    background-color var(--transition-fast),
    color var(--transition-fast);
}

.news-content {
  min-width: 0;
  flex: 1;
}

.news-item:hover {
  background: var(--color-surface-soft);
  color: var(--color-primary);
}

.news-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 20px;
}

.news-type {
  min-width: 64px;
  padding: 5px 10px;
  border-radius: var(--radius-xs);
  background: var(--color-primary-soft);
  color: #6266a6;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.news-title {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.news-summary {
  margin: 8px 0 0 84px;
  overflow: hidden;
  color: var(--color-muted);
  font-size: 13px;
  line-height: 1.6;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-date {
  flex-shrink: 0;
  color: var(--color-muted);
  font-size: 13px;
}

@media (max-width: 600px) {
  .section {
    width: calc(100% - 32px);
    margin: 56px auto;
    padding: 16px;
  }

  .section-header {
    align-items: flex-end;
    gap: 16px;
  }

  .news-item {
    padding: 16px 10px;
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .news-main {
    width: 100%;
    align-items: flex-start;
    gap: 12px;
  }

  .news-summary {
    margin-left: 0;
    white-space: normal;
  }

  .news-title {
    min-width: 0;
    line-height: 1.6;
  }

  .news-date {
    align-self: flex-end;
  }
}
</style>
