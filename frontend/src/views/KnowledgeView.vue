<template>
  <main class="page">
    <div class="page-header">
      <span>KNOWLEDGE</span>

      <h1>操作知识</h1>

      <p>
        基于内部知识库快速查询平台操作方法、常见问题及业务处理流程。
      </p>
    </div>

    <section class="knowledge-card">
      <div class="icon">AI</div>

      <div>
        <h2>智能知识助手</h2>

        <p>
          已接入内部 Dify 知识库，可通过页面右下角智能助手进行业务操作与知识问答。
        </p>
      </div>
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
  margin-bottom: 36px;
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
  max-width: 720px;
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.knowledge-card {
  max-width: 860px;

  display: flex;
  align-items: center;
  gap: 24px;

  padding: 38px;

  border: 1px solid var(--color-border);
  border-radius: 14px;

  background:
    radial-gradient(
      circle at 90% 18%,
      rgba(91, 91, 214, 0.09),
      transparent 28%
    ),
    linear-gradient(135deg, #fbfdff, #f1f5fc);

  box-shadow: var(--shadow-soft);
}

.icon {
  width: 64px;
  height: 64px;

  flex: 0 0 64px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: 1px solid rgba(216, 225, 242, 0.86);
  border-radius: var(--radius-md);

  background:
    linear-gradient(
      145deg,
      rgba(255, 255, 255, 0.94),
      rgba(229, 235, 255, 0.84)
    );
  color: var(--color-primary);

  font-weight: 700;

  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.96),
    0 7px 16px rgba(76, 85, 170, 0.1);
}

.knowledge-card h2 {
  margin: 0 0 10px;
  color: var(--color-text);
  font-size: 22px;
}

.knowledge-card p {
  max-width: 650px;
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.8;
}

@media (max-width: 600px) {
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

  .knowledge-card {
    padding: 24px;
    align-items: flex-start;
    gap: 18px;
  }

  .icon {
    width: 52px;
    height: 52px;
    flex-basis: 52px;
    border-radius: var(--radius-md);
  }

  .knowledge-card h2 {
    font-size: 19px;
  }
}
</style>
