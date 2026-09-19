<script setup>
import ToolGrid from '../components/ToolGrid.vue'
</script>

<template>
  <main class="page">
    <div class="page-header">
      <span>AI TOOLS</span>
      <h1>AI 工具中心</h1>
      <p>集中访问信息运维日常使用的智能化与业务辅助工具。</p>
    </div>

    <ToolGrid detailed />
  </main>
</template>

<style scoped>
.page {
  padding-top: 56px;
}

.page-header {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 0 auto;
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

@media (max-width: 600px) {
  .page {
    padding-top: 40px;
  }

  .page-header {
    width: calc(100% - 32px);
  }

  .page-header h1 {
    font-size: 32px;
  }
}
</style>
