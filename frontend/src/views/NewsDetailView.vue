<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import newsList from '../data/news.json'

const route = useRoute()

const news = computed(() => {
  return newsList.find(
    (item) => String(item.id) === String(route.params.id),
  )
})

const sourceUrl = computed(() => {
  if (
    news.value?.sourceType !== 'external' ||
    !news.value.source ||
    !news.value.sourceUrl
  ) {
    return ''
  }

  try {
    const url = new URL(news.value.sourceUrl)

    return ['http:', 'https:'].includes(url.protocol)
      ? url.href
      : ''
  } catch {
    return ''
  }
})
</script>

<template>
  <main class="detail-page">
    <div
      v-if="news"
      class="article"
    >
      <RouterLink
        to="/news"
        class="back-link"
      >
        ← 返回新闻动态
      </RouterLink>

      <header class="article-header">
        <div class="meta">
          <span class="type">{{ news.type }}</span>
          <time :datetime="news.date">{{ news.date }}</time>
        </div>

        <h1>{{ news.title }}</h1>

        <p class="summary">{{ news.summary }}</p>

        <div
          v-if="news.keywords?.length"
          class="keywords"
          aria-label="关键词"
        >
          <span
            v-for="keyword in news.keywords"
            :key="keyword"
          >
            {{ keyword }}
          </span>
        </div>
      </header>

      <section
        v-if="news.content?.length"
        class="content"
        aria-label="新闻正文"
      >
        <p
          v-for="(paragraph, index) in news.content"
          :key="index"
        >
          {{ paragraph }}
        </p>
      </section>

      <footer
        v-if="news.sourceType === 'external' && news.source"
        class="source-info"
      >
        <span>来源：{{ news.source }}</span>

        <a
          v-if="sourceUrl"
          :href="sourceUrl"
          target="_blank"
          rel="noopener noreferrer"
        >
          查看原文 →
        </a>
      </footer>
    </div>

    <section
      v-else
      class="not-found"
    >
      <h1>未找到该新闻</h1>
      <p>该新闻可能已被移除，或访问地址有误。</p>
      <RouterLink to="/news">返回新闻动态</RouterLink>
    </section>
  </main>
</template>

<style scoped>
.detail-page {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 0 96px;
}

.article {
  max-width: 860px;
  margin: 0 auto;
}

.back-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;

  transition: color var(--transition-fast);
}

.back-link:hover {
  color: var(--color-primary);
}

.article-header {
  padding: 42px 0 36px;
  border-bottom: 1px solid var(--color-border);
}

.meta {
  display: flex;
  align-items: center;
  gap: 14px;

  color: var(--color-muted);
  font-size: 13px;
}

.type {
  padding: 5px 10px;
  border-radius: var(--radius-xs);
  background: var(--color-primary-soft);
  color: #6266a6;
  font-weight: 600;
}

h1 {
  margin: 22px 0 18px;

  color: var(--color-text);
  font-size: 40px;
  line-height: 1.3;
}

.summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 18px;
  line-height: 1.8;
}

.keywords {
  margin-top: 24px;

  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keywords span {
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: #f1f3f6;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.content {
  padding: 38px 0;
}

.content p {
  margin: 0 0 22px;
  color: var(--color-text-secondary);
  font-size: 17px;
  line-height: 1.85;
}

.content p:last-child {
  margin-bottom: 0;
}

.source-info {
  padding: 22px 24px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
  color: var(--color-text-secondary);
  font-size: 14px;

  box-shadow: var(--shadow-soft);
}

.source-info a {
  flex-shrink: 0;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

.not-found {
  max-width: 860px;
  margin: 80px auto 0;
  padding: 64px 24px;

  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);

  text-align: center;
}

.not-found h1 {
  margin: 0 0 12px;
  font-size: 32px;
}

.not-found p {
  margin: 0 0 24px;
  color: var(--color-text-secondary);
}

.not-found a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}

@media (max-width: 600px) {
  .detail-page {
    width: calc(100% - 32px);
    padding: 32px 0 64px;
  }

  .article-header {
    padding: 30px 0 28px;
  }

  h1 {
    margin: 18px 0 14px;
    font-size: 30px;
  }

  .summary {
    font-size: 16px;
  }

  .content {
    padding: 30px 0;
  }

  .content p {
    font-size: 16px;
    line-height: 1.9;
  }

  .source-info {
    align-items: flex-start;
    flex-direction: column;
  }

  .not-found {
    margin-top: 40px;
    padding: 48px 20px;
  }
}
</style>
