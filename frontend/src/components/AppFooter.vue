<template>
  <footer class="footer">
    <div class="footer-inner">
      <div>
        <div class="footer-title">信息运维部智能助手平台</div>
        <div class="footer-description">智能问答 · 操作知识 · AI 工具</div>
      </div>

      <div class="footer-meta">
        <span>信息运维部 · 2026</span>
        <span>V1.0</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-soft);
}

.footer-inner {
  width: calc(100% - 48px);
  max-width: 1200px;
  min-height: 96px;
  margin: 0 auto;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
}

.footer-title {
  color: var(--color-text-secondary);
  font-size: 15px;
  font-weight: 600;
}

.footer-description {
  margin-top: 7px;
  color: var(--color-muted);
  font-size: 13px;
}

.footer-meta {
  display: flex;
  align-items: center;
  gap: 20px;

  color: var(--color-muted);
  font-size: 12px;
}

@media (max-width: 600px) {
  .footer-inner {
    width: calc(100% - 32px);
    min-height: 120px;
    padding: 22px 0;

    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    gap: 16px;
  }
}
</style>
