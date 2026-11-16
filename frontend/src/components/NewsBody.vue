<script>
import { h } from 'vue'
import { markdownNodes } from '../utils/newsMarkdown'

export default {
  props: {
    content: { type: String, default: '' },
    sourceType: { type: String, default: '' },
    title: { type: String, default: '' },
  },
  setup(props) {
    return () => {
      const markdown = props.sourceType === '新能源行业早报'
      const children = markdown ? markdownNodes(props.content, props.title) : props.content
        .split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => h('p', line))
      return h('section', { class: ['content', { 'news-markdown': markdown }], 'aria-label': '新闻正文' }, children)
    }
  },
}
</script>

<style scoped>
.content { padding: 38px 0; }
.content p { margin: 0 0 22px; color: var(--color-text-secondary); font-size: 17px; line-height: 1.85; }
.content p:last-child { margin-bottom: 0; }
.news-markdown { min-width: 0; max-width: 860px; overflow-wrap: anywhere; color: var(--color-text-secondary); font-size: 17px; line-height: 1.85; }
.news-markdown :deep(h1), .news-markdown :deep(h2), .news-markdown :deep(h3), .news-markdown :deep(h4), .news-markdown :deep(h5), .news-markdown :deep(h6) { color: var(--color-text); line-height: 1.5; margin: 1.6em 0 .7em; }
.news-markdown :deep(h1) { font-size: 1.7em; }
.news-markdown :deep(h2) { font-size: 1.4em; }
.news-markdown :deep(h3) { font-size: 1.2em; }
.news-markdown :deep(h4) { font-size: 1.05em; }
.news-markdown :deep(p), .news-markdown :deep(ul), .news-markdown :deep(ol) { margin: 0 0 1.2em; }
.news-markdown :deep(ul), .news-markdown :deep(ol) { padding-left: 1.6em; }
.news-markdown :deep(li) { margin: .35em 0; }
.news-markdown :deep(a) { color: var(--color-primary); text-decoration: underline; text-underline-offset: .2em; overflow-wrap: anywhere; }
.news-markdown :deep(hr) { border: 0; border-top: 1px solid var(--color-border); margin: 2em 0; }
.news-markdown :deep(code) { white-space: pre-wrap; overflow-wrap: anywhere; background: var(--color-surface-soft); padding: .1em .3em; border-radius: 4px; font-size: .9em; }
.news-markdown :deep(pre) { max-width: 100%; white-space: pre-wrap; }
.news-markdown :deep(blockquote) { margin: 1em 0; padding-left: 1em; border-left: 3px solid var(--color-border); }
@media (max-width: 600px) {
  .content { padding: 30px 0; }
  .content p, .news-markdown { font-size: 16px; line-height: 1.9; }
}
</style>
