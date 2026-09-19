<script setup>
import {
  computed,
  ref,
} from 'vue'
import { RouterLink } from 'vue-router'

import newsList from '../data/news.json'

const failedImageIds = ref([])

const sortedNews = computed(() =>
  [...newsList].sort((first, second) =>
    String(second.date).localeCompare(String(first.date)),
  ),
)

function getTypeClass(type) {
  return {
    通知: 'type-notice',
    宣贯: 'type-guidance',
    行业动态: 'type-industry',
  }[type] || 'type-default'
}

function hasNewsImage(news) {
  return (
    typeof news.image === 'string' &&
    news.image.startsWith('/images/news/') &&
    !news.image.startsWith('//') &&
    !failedImageIds.value.includes(news.id)
  )
}

function handleImageError(newsId) {
  if (!failedImageIds.value.includes(newsId)) {
    failedImageIds.value = [...failedImageIds.value, newsId]
  }
}
</script>

<template>
  <main class="page">
    <div class="page-header">
      <span>NEWS</span>
      <h1>新闻动态</h1>
      <p>内部通知、信息宣贯及行业动态统一展示。</p>
    </div>

    <div
      v-if="sortedNews.length"
      class="news-grid"
    >
      <article
        v-for="news in sortedNews"
        :key="news.id"
        class="news-card"
      >
        <RouterLink
          :to="`/news/${news.id}`"
          class="news-card-link"
        >
          <div class="news-cover">
            <img
              v-if="hasNewsImage(news)"
              :src="news.image"
              :alt="news.title"
              @error="handleImageError(news.id)"
            >

            <div
              v-else
              class="default-cover"
              :class="getTypeClass(news.type)"
            >
              <span class="cover-mark">NEWS</span>
              <strong>{{ news.type }}</strong>
            </div>
          </div>

          <div class="news-card-body">
            <div class="news-meta">
              <span
                class="type"
                :class="getTypeClass(news.type)"
              >
                {{ news.type }}
              </span>
              <time :datetime="news.date">{{ news.date }}</time>
            </div>

            <h2>{{ news.title }}</h2>

            <p>{{ news.summary }}</p>

            <span class="detail-link">查看详情 →</span>
          </div>
        </RouterLink>
      </article>
    </div>

    <section
      v-else
      class="empty-state"
    >
      暂无新闻动态
    </section>
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
  font-size: 40px;
  line-height: 1.25;
  color: var(--color-text);
}

.page-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}

.news-card {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  overflow: hidden;

  box-shadow: var(--shadow-soft);

  transition:
    transform var(--transition-normal),
    border-color var(--transition-normal),
    box-shadow var(--transition-normal);
}

.news-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-hover);
}

.news-card-link {
  height: 100%;

  display: flex;
  flex-direction: column;

  color: inherit;
  text-decoration: none;
}

.news-cover {
  position: relative;

  width: 100%;
  aspect-ratio: 16 / 9;

  overflow: hidden;
  background: #edf3fb;
}

.news-cover img,
.default-cover {
  width: 100%;
  height: 100%;
}

.news-cover img {
  display: block;
  object-fit: cover;
}

.default-cover {
  position: relative;

  padding: 24px;

  display: flex;
  align-items: flex-end;
  justify-content: space-between;

  background:
    radial-gradient(
      circle at 78% 24%,
      rgba(91, 91, 214, 0.1),
      transparent 30%
    ),
    linear-gradient(135deg, #f5f8fd 0%, #e8eef9 100%);
  color: #47617f;
}

.default-cover::before {
  content: "";

  position: absolute;
  top: 22%;
  right: 12%;

  width: 84px;
  height: 84px;

  border: 1px solid rgba(91, 91, 214, 0.16);
  border-radius: 50%;
}

.default-cover::after {
  content: "";

  position: absolute;
  top: 37%;
  right: 21%;

  width: 54px;
  height: 1px;

  transform: rotate(-28deg);
  background: rgba(91, 91, 214, 0.2);
}

.cover-mark,
.default-cover strong {
  position: relative;
  z-index: 1;
}

.cover-mark {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.6px;
}

.default-cover strong {
  font-size: 18px;
  font-weight: 600;
}

.default-cover.type-guidance {
  background: linear-gradient(135deg, #f7f5fc 0%, #eeeafb 100%);
  color: #67558b;
}

.default-cover.type-industry {
  background: linear-gradient(135deg, #f2f8f6 0%, #e5f2ed 100%);
  color: #3e715f;
}

.news-card-body {
  min-width: 0;
  flex: 1;
  padding: 22px;

  display: flex;
  flex-direction: column;
}

.news-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  color: var(--color-muted);
  font-size: 12px;
}

.type {
  padding: 5px 10px;
  border-radius: 6px;
  background: #edf4ff;
  color: #476d9f;
  font-weight: 600;
}

.type.type-guidance {
  background: #f2eefb;
  color: #725f99;
}

.type.type-industry {
  background: #eaf5f0;
  color: #3f765f;
}

.type.type-default {
  background: #f1f3f6;
  color: var(--color-text-secondary);
}

.news-card h2 {
  min-height: 54px;
  margin: 0 0 10px;

  display: -webkit-box;
  overflow: hidden;

  font-size: 18px;
  line-height: 1.5;
  color: var(--color-text);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.news-card p {
  flex: 1;
  min-height: 71px;
  margin: 0 0 18px;

  display: -webkit-box;
  overflow: hidden;

  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.detail-link {
  color: var(--color-primary);
  font-size: 14px;
  font-weight: 600;
}

.empty-state {
  padding: 72px 24px;

  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface-soft);
  color: var(--color-muted);
  text-align: center;
}

@media (max-width: 1099px) {
  .news-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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

  .news-grid {
    grid-template-columns: 1fr;
    gap: 18px;
  }
}
</style>
