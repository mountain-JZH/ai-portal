<script setup>
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

// Enable future entries only after their pages and routes are implemented.
const navigation = [
  { label: '首页', to: '/', enabled: true },
  { label: '新闻动态', to: '/news', enabled: true },
  { label: '项目看板', to: '/projects', enabled: false },
  { label: '互通有无', to: '/exchange', enabled: true },
  { label: 'AI 工具', to: '/tools', enabled: true },
  { label: '后台', to: '/admin', enabled: true, admin: true },
]
const availableNavigation = navigation.filter((item) => item.enabled)

function isCurrent(target) {
  return route.path === target || (target !== '/' && route.path.startsWith(`${target}/`))
}
</script>

<template>
  <header class="header">
    <div class="header-inner">
      <RouterLink to="/" class="brand" aria-label="信息运维部智能助手平台，返回首页">
        <span class="brand-title"><mark>智能助手</mark>平台</span>
      </RouterLink>

      <nav class="nav" aria-label="门户主导航">
        <div
          v-for="item in availableNavigation"
          :key="item.to"
          class="nav-item"
          :class="{ 'nav-item-admin': item.admin }"
        >
          <RouterLink
            :to="item.to"
            class="nav-link"
            :class="{ 'is-current': isCurrent(item.to) }"
            :aria-current="isCurrent(item.to) ? 'page' : undefined"
            :data-label="item.label"
          >
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
      </nav>

      <RouterLink to="/" class="brand-signature" aria-label="AI Portal，返回首页">
        <span class="brand-wordmark">AI <span class="portal-word">PORTAL</span></span>
        <span class="brand-subtitle">信息运维部</span>
      </RouterLink>
    </div>
  </header>
</template>

<style scoped>
.header {
  --header-bg: #ffffff;
  --header-foreground: #22292c;
  --header-foreground-muted: #6d5b55;
  --header-active: #f7b334;
  --header-brand-green: #8dfc08;

  background: var(--header-bg);
  color: var(--header-foreground);
  border-bottom: 1px solid #e6e9ea;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.header-inner {
  width: calc(100% - 96px);
  max-width: 1600px;
  min-height: 87px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto minmax(140px, 0.55fr);
  gap: 42px;
  align-items: first baseline;
  align-content: center;
}

.brand,
.brand-signature {
  display: block;
  min-width: 0;
  color: var(--header-foreground);
  text-decoration: none;
  white-space: nowrap;
}

.brand {
  justify-self: start;
}

.brand-title {
  font-size: 25px;
  font-weight: 700;
  line-height: 1.4;
}

.brand-title mark {
  background: linear-gradient(transparent 62%, var(--header-active) 62%);
  color: inherit;
  padding-right: 3px;
}

.brand-signature {
  justify-self: end;
  text-align: right;
}

.brand-wordmark {
  display: block;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.6px;
}

.portal-word {
  background: linear-gradient(transparent 45%, var(--header-brand-green) 45%);
  padding-right: 4px;
}

/* The signature's first line supplies its baseline; the subtitle stays in flow. */
.brand-subtitle {
  display: block;
  margin-top: 4px;
  color: var(--header-foreground-muted);
  font-size: 11px;
  font-weight: 400;
  line-height: 1.5;
  letter-spacing: 0.03em;
}

.nav {
  min-width: 0;
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  justify-content: flex-end;
  column-gap: 26px;
  row-gap: 8px;
}

.nav-item {
  display: flex;
  align-items: baseline;
}

.nav-item-admin {
  margin-left: 4px;
  padding-left: 22px;
  border-left: 1px solid #d9dfe1;
  height: 22px;
}

.nav-link {
  position: relative;
  display: inline-grid;
  align-items: center;
  justify-items: center;
  min-height: 48px;
  padding: 10px 2px;
  color: var(--header-foreground);
  font-size: 15px;
  font-weight: 500;
  line-height: 24px;
  text-decoration: none;
  white-space: nowrap;
  transition: color 200ms ease;
}

.nav-link span,
.nav-link::before {
  grid-area: 1 / 1;
}

/* Reserve the active weight's width so route changes do not shift neighbours. */
.nav-link::before {
  content: attr(data-label);
  font-weight: 600;
  visibility: hidden;
}

.nav-link::after {
  content: "";
  position: absolute;
  bottom: 3px;
  right: 2px;
  left: 2px;
  height: 2px;
  background: var(--header-active);
  opacity: 0;
  transition: opacity 200ms ease;
}

.nav-link:hover {
  color: var(--header-foreground-muted);
}

.nav-link:hover::after {
  opacity: 0.45;
}

.nav-link.is-current {
  font-weight: 600;
}

.nav-link.is-current::after {
  opacity: 1;
}

.nav-link:active {
  color: var(--header-foreground-muted);
  opacity: 0.72;
}

.brand:focus-visible,
.brand-signature:focus-visible,
.nav-link:focus-visible {
  outline: 2px solid var(--header-foreground);
  outline-offset: 5px;
  border-radius: 2px;
}

@media (max-width: 1250px) {
  .header-inner {
    width: calc(100% - 48px);
    grid-template-columns: minmax(200px, 1fr) auto minmax(100px, 0.45fr);
    gap: 20px;
  }

  .nav {
    column-gap: 20px;
  }
}

@media (max-width: 1000px) {
  .header-inner {
    grid-template-columns: minmax(0, 1fr) auto;
    padding: 14px 0 6px;
    gap: 10px;
  }

  .brand-signature {
    grid-column: 2;
    grid-row: 1;
  }

  .nav {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}

@media (max-width: 600px) {
  .header-inner {
    width: calc(100% - 32px);
    padding: 14px 0 8px;
  }

  .brand-title {
    font-size: 22px;
  }

  .brand-wordmark {
    font-size: 18px;
  }

  .nav {
    justify-content: flex-start;
    column-gap: 20px;
    row-gap: 6px;
  }

  .nav-item-admin {
    margin-left: 0;
    padding-left: 16px;
  }

  .nav-link {
    min-height: 44px;
    font-size: 14px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .nav-link,
  .nav-link::after {
    transition: none;
  }
}
</style>
