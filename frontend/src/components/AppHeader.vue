<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'

const latestAnnouncement = ref(null)
const announcementLoading = ref(true)
const announcementError = ref(false)

async function loadLatestAnnouncement() {
  announcementLoading.value = true
  announcementError.value = false

  try {
    const response = await fetch(`${API_BASE_URL}/api/announcements`, {
      cache: 'no-store',
    })

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    const data = await response.json()
    latestAnnouncement.value = Array.isArray(data) ? data[0] || null : null
  } catch (error) {
    console.error('平台公告加载失败：', error)
    latestAnnouncement.value = null
    announcementError.value = true
  } finally {
    announcementLoading.value = false
  }
}

onMounted(loadLatestAnnouncement)
</script>

<template>
  <header class="header">
    <div class="header-inner">

      <RouterLink
        to="/"
        class="brand"
      >
        <div class="brand-logo">
          AI
        </div>

        <div class="brand-copy">
          <div class="brand-title">
            信息运维部智能助手平台
          </div>

          <div class="brand-subtitle">
            Information & Operations AI Portal
          </div>
        </div>
      </RouterLink>

      <div
        class="header-announcement"
        :class="{ 'is-placeholder': !latestAnnouncement }"
        aria-label="最新平台公告"
        aria-live="polite"
      >
        <template v-if="latestAnnouncement">
          <span class="announcement-label">平台公告</span>
          <span class="announcement-title">
            {{ latestAnnouncement.title }}
          </span>
          <time :datetime="latestAnnouncement.date">
            {{ latestAnnouncement.date }}
          </time>
        </template>

        <span v-else class="announcement-status">
          {{ announcementLoading
            ? '正在加载平台公告...'
            : announcementError ? '平台公告暂时无法加载' : '暂无平台公告' }}
        </span>
      </div>

      <nav class="nav">
        <RouterLink to="/">
          首页
        </RouterLink>

        <RouterLink to="/news">
          新闻动态
        </RouterLink>

        <RouterLink to="/admin">
          管理后台
        </RouterLink>

        <RouterLink to="/tools">
          AI 工具
        </RouterLink>
      </nav>

    </div>
  </header>
</template>

<style scoped>
.header {
  height: 72px;

  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.88);

  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}

.header-inner {
  width: calc(100% - 48px);
  max-width: 1200px;
  height: 100%;

  margin: 0 auto;

  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  min-width: 0;
  flex-shrink: 0;

  display: flex;
  align-items: center;
  gap: 12px;

  text-decoration: none;
}

.brand-copy {
  min-width: 0;
}

.brand-logo {
  width: 40px;
  height: 40px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: var(--radius-md);

  background: linear-gradient(145deg, #536fd9, #655ce7);
  color: white;

  font-weight: 700;

  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.34),
    0 5px 14px rgba(76, 85, 170, 0.16);
}

.brand-title {
  color: var(--color-text);

  font-size: 17px;
  font-weight: 650;
}

.brand-subtitle {
  margin-top: 2px;

  color: var(--color-muted);

  font-size: 11px;
}

.header-announcement {
  min-width: 0;
  flex: 1;

  display: flex;
  align-items: center;
  gap: 9px;

  padding: 7px 10px;

  border: 1px solid rgba(216, 225, 242, 0.84);
  border-radius: var(--radius-sm);
  background: var(--color-glass);
  color: var(--color-text-secondary);
  font-size: 12px;

  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);

  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.announcement-label {
  flex-shrink: 0;
  padding: 4px 7px;

  border-radius: var(--radius-xs);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}

.announcement-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-announcement time {
  flex-shrink: 0;
  color: var(--color-muted);
  font-size: 11px;
}

.header-announcement.is-placeholder {
  color: var(--color-muted);
}

.announcement-status {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav {
  flex-shrink: 0;

  display: flex;
  gap: 32px;
}

.nav a {
  position: relative;

  padding: 26px 0 24px;

  color: var(--color-text-secondary);

  text-decoration: none;

  font-size: 14px;

  transition: color var(--transition-fast);
}

.nav a:hover {
  color: var(--color-text);
}

.nav a.router-link-active {
  color: var(--color-text);
  font-weight: 600;
}

.nav a.router-link-active::after {
  content: "";

  position: absolute;

  right: 0;
  bottom: -1px;
  left: 0;

  height: 2px;

  background: var(--color-primary);
}

@media (max-width: 1100px) {
  .header-announcement time {
    display: none;
  }
}

@media (max-width: 1024px) {
  .header-announcement {
    display: none;
  }

  .header-inner {
    justify-content: space-between;
  }
}

@media (max-width: 760px) {
  .brand-subtitle {
    display: none;
  }

  .nav {
    gap: 16px;
  }
}

@media (max-width: 600px) {
  .header {
    height: auto;
  }

  .header-inner {
    width: calc(100% - 32px);
    padding-top: 12px;

    align-items: stretch;
    flex-direction: column;
    gap: 10px;
  }

  .brand {
    align-self: flex-start;
  }

  .brand-logo {
    width: 34px;
    height: 34px;
    border-radius: 10px;
  }

  .brand-title {
    font-size: 15px;
  }

  .nav {
    width: 100%;
    gap: 0;
    justify-content: space-between;
  }

  .nav a {
    padding: 10px 0 12px;
    font-size: 13px;
  }
}
</style>
