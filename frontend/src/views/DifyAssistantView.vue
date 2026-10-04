<script setup>
const difyEmbedUrl = import.meta.env.VITE_DIFY_EMBED_URL?.trim() || ''
</script>

<template>
  <main class="assistant-page">
    <header class="assistant-header">
      <span>AI ASSISTANT</span>
      <h1>Dify 助手</h1>
      <p>基于部门知识库提供平台操作、业务知识及常见问题辅助查询。</p>
    </header>

    <section class="assistant-content" aria-label="Dify 助手工作区">
      <iframe
        v-if="difyEmbedUrl"
        class="assistant-frame"
        :src="difyEmbedUrl"
        title="Dify 助手"
        allow="microphone; clipboard-write"
      />

      <div v-else class="assistant-empty" role="status">
        <strong>Dify 助手暂未配置。</strong>
        <p>请配置 VITE_DIFY_EMBED_URL 后重新构建前端。</p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.assistant-page {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 0 56px;
}

.assistant-header {
  margin-bottom: 24px;
}

.assistant-header > span {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
}

.assistant-header h1 {
  margin: 12px 0 10px;
  color: var(--color-text);
  font-size: 40px;
  line-height: 1.2;
}

.assistant-header p {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.assistant-content {
  width: 100%;
  min-width: 0;
  height: calc(100vh - 248px);
  min-height: 700px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.assistant-frame {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
}

.assistant-empty {
  width: 100%;
  height: 100%;
  padding: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: var(--color-text-secondary);
  text-align: center;
}

.assistant-empty strong {
  color: var(--color-text);
  font-size: 18px;
}

.assistant-empty p {
  margin: 10px 0 0;
  color: var(--color-muted);
  font-size: 14px;
}

@media (max-width: 600px) {
  .assistant-page {
    width: calc(100% - 32px);
    padding: 28px 0 40px;
  }

  .assistant-header {
    margin-bottom: 18px;
  }

  .assistant-header h1 {
    font-size: 32px;
  }

  .assistant-content {
    height: calc(100vh - 190px);
    height: calc(100dvh - 190px);
    min-height: 620px;
    border-radius: var(--radius-md);
  }

  .assistant-empty {
    padding: 24px 18px;
  }
}
</style>
