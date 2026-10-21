<script setup>
import { employeeFetch as fetch } from '../utils/employeeAuth'
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import SectionMasthead from './SectionMasthead.vue'
import ChevronRight from './ChevronRight.vue'

defineProps({
  mastheadImage: { type: String, default: '' },
  mastheadFallbackImage: { type: String, default: '' },
  mastheadTextMode: { type: String, default: 'dark' },
})

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
  <section class="home-news-section" aria-label="最新动态">
    <SectionMasthead
      title="最新动态"
      description="关注内部通知、信息宣贯及行业动态"
      to="/news"
      :image="mastheadImage"
      :fallback-image="mastheadFallbackImage"
      :text-mode="mastheadTextMode"
      navigation-label="全部"
      navigation-aria-label="查看全部新闻"
    />

    <div class="news-body" :aria-busy="loading">
      <div v-if="loading" class="status-message" role="status">
        正在加载最新动态...
      </div>
      <div v-else-if="errorMessage" class="status-message error-message" role="alert">
        {{ errorMessage }}
      </div>
      <div v-else-if="latestNews.length === 0" class="status-message" role="status">
        暂无新闻
      </div>
      <div v-else class="news-list">
        <RouterLink
          v-for="news in latestNews"
          :key="news.id"
          :to="`/news/${news.id}`"
          class="news-item"
          :aria-label="news.title"
        >
          <div class="news-meta">
            <span class="news-type">{{ news.type }}</span>
            <time class="news-date" :datetime="news.date">{{ news.date }}</time>
          </div>
          <div class="news-content">
            <h3 class="news-title">{{ news.title }}</h3>
            <p class="news-summary">{{ news.summary }}</p>
          </div>
          <ChevronRight class="news-arrow" />
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-news-section {
  --masthead-inline-padding: 32px;
  --masthead-navigation-slot: 28px;
  width: 100%;
  min-width: 0;
  height: var(--home-slot-height, 464px);
  display: grid;
  grid-template-rows: var(--home-masthead-height, 128px) minmax(0, 1fr);
  font-family: var(--home-font, inherit);
  color: var(--home-text, #22292c);
}

.news-body {
  min-width: 0;
  height: calc(var(--home-news-row-height, 112px) * 3);
}

.news-list {
  display: grid;
  grid-template-rows: repeat(3, var(--home-news-row-height, 112px));
  height: 100%;
}

.status-message {
  display: grid;
  place-items: center;
  height: 100%;
  padding: 24px;
  color: var(--home-muted, #697378);
  font-size: 14px;
  text-align: center;
}

.error-message { color: #a23e3e; }

.news-item {
  display: grid;
  grid-template-columns: 78px minmax(0, 1fr) var(--masthead-navigation-slot);
  align-items: center;
  gap: 16px;
  height: var(--home-news-row-height, 112px);
  min-width: 0;
  padding: 10px 20px;
  padding-right: var(--masthead-inline-padding);
  overflow: hidden;
  border-bottom: 1px solid var(--home-border, #e5e8e9);
  color: inherit;
  text-decoration: none;
  transition: background-color var(--home-motion, 220ms) var(--home-ease, ease);
}

.news-item:last-child { border-bottom: 0; }

.news-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  min-width: 0;
}

.news-type {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
  color: var(--home-earth, #6d5b55);
  font-size: 12px;
  line-height: 18px;
}

.news-date {
  color: var(--home-muted, #697378);
  font-size: 12px;
  line-height: 18px;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.news-content { min-width: 0; }

.news-title,
.news-summary {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}

.news-title {
  margin: 0;
  color: var(--home-text, #22292c);
  font-size: 16px;
  font-weight: 600;
  line-height: 21px;
}

.news-summary {
  margin: 5px 0 0;
  color: var(--home-secondary, #586165);
  font-size: 13px;
  line-height: 20px;
}

.news-arrow {
  justify-self: center;
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: .8;
  pointer-events: none;
  transition: transform var(--home-motion, 220ms) var(--home-ease, ease);
}

.news-item:hover { background: var(--home-subtle, #f5f6f7); }
.news-item:hover .news-title { color: #394348; }
.news-item:active { background: #eceff0; }
.news-item:focus-visible { outline: 2px solid var(--home-earth, #6d5b55); outline-offset: -3px; }
.news-item:hover .news-arrow,
.news-item:focus-visible .news-arrow { transform: translateX(3px); opacity: 1; }

@media (max-width: 768px) {
  .home-news-section { height: auto; grid-template-rows: auto minmax(0, 1fr); }
}

@media (max-width: 480px) {
  .home-news-section { --masthead-inline-padding: 20px; }
  .news-item { gap: 10px; padding-left: 4px; }
  .news-title { font-size: 14px; line-height: 20px; }
}

@media (prefers-reduced-motion: reduce) {
  .news-item, .news-arrow { transition: none; }
  .news-item:hover .news-arrow,
  .news-item:focus-visible .news-arrow { transform: none; }
}
</style>
