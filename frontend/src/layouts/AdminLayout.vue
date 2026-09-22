<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const isDashboardActive = computed(() => route.name === 'admin-dashboard')
const isNewsActive = computed(() => route.path.startsWith('/admin/news'))
</script>

<template>
  <div class="admin-layout">
    <header class="admin-header">
      <div class="admin-header-inner">
        <RouterLink to="/admin" class="admin-brand">
          <span class="admin-brand-mark" aria-hidden="true">AI</span>
          <span class="admin-brand-copy">
            <strong>信息运维部智能助手平台</strong>
            <small>管理后台</small>
          </span>
        </RouterLink>

        <RouterLink to="/" class="portal-link">返回门户 →</RouterLink>
      </div>
    </header>

    <div class="admin-shell">
      <aside class="admin-sidebar">
        <nav aria-label="后台管理导航">
          <RouterLink
            to="/admin"
            class="admin-nav-link"
            :class="{ active: isDashboardActive }"
          >
            管理首页
          </RouterLink>

          <div class="admin-nav-group">
            <span class="admin-nav-label">内容管理</span>
            <RouterLink
              to="/admin/news"
              class="admin-nav-link admin-nav-child"
              :class="{ active: isNewsActive }"
            >
              新闻管理
            </RouterLink>
          </div>

          <div class="admin-coming-soon" aria-label="后续管理能力">
            <span>更多管理能力</span>
            <small>即将开放</small>
          </div>
        </nav>

        <RouterLink to="/" class="sidebar-portal-link">← 返回门户</RouterLink>
      </aside>

      <div class="admin-content" role="main">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background:
    linear-gradient(180deg, rgba(238, 242, 255, 0.58), transparent 220px),
    var(--color-bg);
}

.admin-header {
  min-height: 68px;
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.94);
}

.admin-header-inner {
  width: calc(100% - 48px);
  max-width: 1440px;
  min-height: 68px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.admin-brand {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: inherit;
  text-decoration: none;
}

.admin-brand-mark {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: linear-gradient(145deg, #536fd9, #655ce7);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 5px 14px rgba(76, 85, 170, 0.16);
}

.admin-brand-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-brand-copy strong {
  overflow: hidden;
  color: var(--color-text);
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-brand-copy small {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

.portal-link,
.sidebar-portal-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
}

.portal-link:hover,
.sidebar-portal-link:hover {
  color: var(--color-primary);
}

.admin-shell {
  width: calc(100% - 48px);
  max-width: 1440px;
  min-height: calc(100vh - 69px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
}

.admin-sidebar {
  min-width: 0;
  padding: 32px 20px 28px 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 40px;
  border-right: 1px solid var(--color-border);
}

.admin-sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-nav-group {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-nav-label {
  padding: 0 12px 3px;
  color: var(--color-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.admin-nav-link {
  min-height: 42px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition:
    color var(--transition-fast),
    background-color var(--transition-fast),
    border-color var(--transition-fast);
}

.admin-nav-link:hover {
  color: var(--color-primary);
  background: rgba(238, 242, 255, 0.6);
}

.admin-nav-link.active {
  border-color: rgba(91, 91, 214, 0.16);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.admin-nav-child::before {
  margin-right: 8px;
  content: "└";
  color: var(--color-muted);
  font-weight: 400;
}

.admin-coming-soon {
  margin-top: 20px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  font-size: 12px;
}

.admin-coming-soon small {
  flex-shrink: 0;
  color: var(--color-muted);
  font-size: 11px;
}

.admin-content {
  min-width: 0;
  padding: 40px 0 80px 40px;
}

.admin-content :deep(.page) {
  width: 100%;
  max-width: 1200px;
  margin: 0;
  padding: 0;
}

@media (max-width: 1024px) {
  .admin-shell {
    grid-template-columns: 190px minmax(0, 1fr);
  }

  .admin-content {
    padding-left: 28px;
  }
}

@media (max-width: 768px) {
  .admin-header-inner,
  .admin-shell {
    width: calc(100% - 32px);
  }

  .admin-header-inner {
    padding: 10px 0;
  }

  .admin-shell {
    min-height: 0;
    display: block;
  }

  .admin-sidebar {
    padding: 16px 0;
    display: block;
    border-right: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .admin-sidebar nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .admin-nav-group {
    margin: 0;
    display: contents;
  }

  .admin-nav-label,
  .admin-coming-soon,
  .sidebar-portal-link {
    display: none;
  }

  .admin-nav-link {
    justify-content: center;
  }

  .admin-nav-child::before {
    display: none;
  }

  .admin-content {
    padding: 32px 0 64px;
  }
}

@media (max-width: 500px) {
  .admin-header-inner {
    align-items: flex-start;
  }

  .admin-brand-copy strong {
    white-space: normal;
  }

  .portal-link {
    flex-shrink: 0;
    padding-top: 3px;
  }
}

@media (max-width: 360px) {
  .admin-brand-mark {
    display: none;
  }

  .admin-brand-copy strong {
    font-size: 14px;
  }
}
</style>
