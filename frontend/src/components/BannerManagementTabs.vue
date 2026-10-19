<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <nav class="banner-management-tabs" aria-label="Banner 管理分区">
    <RouterLink to="/admin/content/banners" exact-active-class="selected">主 Banner 管理</RouterLink>
    <RouterLink to="/admin/content/banners/sections" exact-active-class="selected">栏目背景图管理</RouterLink>
  </nav>
</template>

<style scoped>
.banner-management-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; border-bottom: 1px solid #e5e8e9; }
a { padding: 12px 16px; color: #586165; font-size: 14px; text-decoration: none; border-bottom: 2px solid transparent; }
a.selected { color: #22292c; font-weight: 600; border-color: #f7b334; }
a:focus-visible { outline: 2px solid #6d5b55; outline-offset: -2px; }
</style>
