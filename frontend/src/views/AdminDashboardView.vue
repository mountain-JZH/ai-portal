<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'

const newsList = ref([])
const loading = ref(true)
const errorMessage = ref('')

const publishedCount = computed(
  () => newsList.value.filter((news) => Number(news.is_published) === 1).length,
)
const unpublishedCount = computed(() => newsList.value.length - publishedCount.value)

async function loadNewsStats() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${API_BASE_URL}/api/admin/news`)

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    const data = await response.json()
    newsList.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('后台新闻统计加载失败：', error)
    errorMessage.value = '新闻统计加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadNewsStats()
})
</script>

<template>
  <section class="dashboard-page">
    <header class="dashboard-header">
      <span>ADMIN DASHBOARD</span>
      <h1>管理首页</h1>
      <p>集中查看门户内容状态，并进入常用管理功能。</p>
    </header>

    <div v-if="loading" class="dashboard-state" role="status">正在加载统计数据...</div>

    <div v-else-if="errorMessage" class="dashboard-state dashboard-state-error" role="alert">
      {{ errorMessage }}
    </div>

    <div v-else class="stats-grid" aria-label="新闻统计">
      <article class="stat-card">
        <span>新闻总数</span>
        <strong>{{ newsList.length }}</strong>
      </article>
      <article class="stat-card">
        <span>已发布</span>
        <strong>{{ publishedCount }}</strong>
      </article>
      <article class="stat-card">
        <span>未发布</span>
        <strong>{{ unpublishedCount }}</strong>
      </article>
    </div>

    <section class="quick-section" aria-labelledby="quick-title">
      <div class="quick-heading">
        <h2 id="quick-title">快捷入口</h2>
        <p>进入当前已经开放的管理功能。</p>
      </div>

      <div class="quick-grid">
        <RouterLink to="/admin/news" class="quick-card">
          <strong>新闻管理</strong>
          <span>维护、发布或下架门户新闻</span>
          <small>进入管理 →</small>
        </RouterLink>
        <RouterLink to="/admin/news/new" class="quick-card">
          <strong>新增新闻</strong>
          <span>创建一条新的门户新闻内容</span>
          <small>开始创建 →</small>
        </RouterLink>
        <RouterLink to="/" class="quick-card">
          <strong>返回门户</strong>
          <span>查看当前公开门户展示效果</span>
          <small>打开门户 →</small>
        </RouterLink>
      </div>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page {
  width: 100%;
  max-width: 1200px;
}

.dashboard-header {
  position: relative;
  margin-bottom: 34px;
  padding-bottom: 20px;
}

.dashboard-header::after {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 42px;
  height: 3px;
  content: "";
  border-radius: 2px;
  background: var(--color-primary);
}

.dashboard-header > span {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
}

.dashboard-header h1 {
  margin: 12px 0 10px;
  color: var(--color-text);
  font-size: 40px;
  line-height: 1.25;
}

.dashboard-header p,
.quick-heading p {
  margin: 0;
  color: var(--color-text-secondary);
}

.stats-grid,
.quick-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card,
.quick-card,
.dashboard-state {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}

.stat-card {
  min-height: 142px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.stat-card span {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.stat-card strong {
  color: var(--color-primary);
  font-size: 38px;
  line-height: 1;
}

.dashboard-state {
  padding: 56px 24px;
  color: var(--color-muted);
  text-align: center;
}

.dashboard-state-error {
  color: #9b4545;
}

.quick-section {
  margin-top: 42px;
}

.quick-heading {
  margin-bottom: 20px;
}

.quick-heading h2 {
  margin: 0 0 8px;
  color: var(--color-text);
  font-size: 22px;
}

.quick-heading p {
  font-size: 14px;
}

.quick-card {
  min-width: 0;
  min-height: 170px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  color: inherit;
  text-decoration: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast);
}

.quick-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}

.quick-card strong {
  color: var(--color-text);
  font-size: 17px;
}

.quick-card span {
  margin-top: 10px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.quick-card small {
  margin-top: auto;
  padding-top: 18px;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

@media (max-width: 900px) {
  .stats-grid,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .stat-card,
  .quick-card {
    min-height: 0;
  }

  .stat-card {
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    margin-bottom: 28px;
  }

  .dashboard-header h1 {
    font-size: 32px;
  }

  .quick-section {
    margin-top: 34px;
  }
}
</style>
