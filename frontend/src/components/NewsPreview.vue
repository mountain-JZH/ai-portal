<script setup>
import { ref } from 'vue'
import NewsBody from './NewsBody.vue'

defineProps({
  title: { type: String, default: '' },
  summary: { type: String, default: '' },
  publishDate: { type: String, default: '' },
  sourceType: { type: String, default: '' },
  content: { type: String, default: '' },
})
const expanded = ref(false)
</script>

<template>
  <div class="preview-control">
    <button type="button" :aria-expanded="expanded" @click="expanded = !expanded">
      {{ expanded ? '收起预览' : '展开预览' }}
    </button>
    <span>预览不会保存或发布内容；内部审校记录请勿粘贴到正文。</span>
  </div>
  <section v-if="expanded" class="news-preview" aria-label="新闻预览">
    <header>
      <p class="preview-meta"><span>{{ sourceType }}</span><time :datetime="publishDate">{{ publishDate }}</time></p>
      <h2>{{ title || '未填写标题' }}</h2>
      <p v-if="summary" class="preview-summary">{{ summary }}</p>
    </header>
    <NewsBody :title="title" :content="content" :source-type="sourceType" />
    <p v-if="!content" class="preview-empty">填写正文后将在此实时预览。</p>
  </section>
</template>

<style scoped>
.preview-control { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin: 24px 0; }
.preview-control button { border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 10px 16px; background: var(--color-surface); color: var(--color-primary); font: inherit; cursor: pointer; }
.preview-control button:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.preview-control span, .preview-empty { font-size: 13px; color: var(--color-text-secondary); }
.news-preview { min-width: 0; padding: 24px; border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow-wrap: anywhere; }
.news-preview header { max-width: 860px; margin: 0 auto; padding-bottom: 24px; border-bottom: 1px solid var(--color-border); }
.news-preview h2 { margin: 20px 0 16px; font-size: 32px; line-height: 1.3; color: var(--color-text); }
.preview-meta { display: flex; flex-wrap: wrap; gap: 14px; font-size: 13px; color: var(--color-text-secondary); }
.preview-summary { font-size: 18px; line-height: 1.8; color: var(--color-text-secondary); }
.news-preview :deep(.content) { margin: 0 auto; }
@media (max-width: 600px) {
  .news-preview { padding: 16px; }
  .news-preview h2 { font-size: 26px; }
  .preview-summary { font-size: 16px; }
}
</style>
