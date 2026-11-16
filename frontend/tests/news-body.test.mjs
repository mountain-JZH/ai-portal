import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { createServer } from 'vite'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
after(() => server.close())
const { default: NewsBody } = await server.ssrLoadModule('/src/components/NewsBody.vue')
const render = (content, sourceType = '新能源行业早报', title = '') => renderToString(createSSRApp(NewsBody, { content, sourceType, title }))

test('ordinary news preserves trimmed nonempty text paragraphs and escaping', async () => {
  const html = await render(' first \n\n **bold**\n<script>alert(1)</script>', '行业资讯')
  assert.match(html, /<p[^>]*>first<\/p><p[^>]*>\*\*bold\*\*<\/p>/)
  assert.match(html, /&lt;script&gt;/)
  assert.doesNotMatch(html, /<strong>|<script>/)
})
test('early brief supports required headings, emphasis, lists, rule and inline code', async () => {
  const html = await render('# 今日速览\n\n## 今日重点\n\n### 江苏及周边动态\n\n#### 行业快讯\n\n**重点**与*关注*和`V2G`\n\n- 甲\n- 乙\n\n1. 第一\n2. 第二\n\n---\n\n持续关注')
  for (const tag of ['h1', 'h2', 'h3', 'h4', 'strong', 'em', 'ul', 'ol', 'li', 'hr', 'code']) assert.match(html, new RegExp(`<${tag}[ >]`))
})
test('only first identical H1 is omitted without modifying source', async () => {
  const source = '# 新能源行业早报｜2026-11-16\n\n## 今日速览\n\n# 后续标题'
  const html = await render(source, '新能源行业早报', '新能源行业早报｜2026-11-16')
  assert.doesNotMatch(html, /<h1[^>]*>新能源行业早报/)
  assert.match(html, /<h1[^>]*>后续标题/)
  assert.ok(source.startsWith('# 新能源行业早报'))
  assert.match(await render('# 不同标题', '新能源行业早报', '外层标题'), /<h1[^>]*>不同标题/)
})
test('HTTP sources are clickable with safe new-window attributes', async () => {
  const html = await render('[来源](https://example.com/article?q=energy)')
  assert.match(html, /href="https:\/\/example.com\/article\?q=energy"/)
  assert.match(html, /target="_blank" rel="noopener noreferrer"/)
})
test('HTML, iframe, event attributes and images never become active nodes', async () => {
  const html = await render('<script>alert(1)</script>\n\n<iframe src="https://example.com"></iframe>\n\n<img src=x onerror=alert(1)>\n\n![图](https://example.com/pixel.png)\n\n<svg onload=alert(1)>')
  assert.doesNotMatch(html, /<(script|iframe|img|svg)\b/)
  assert.match(html, /&lt;script&gt;/)
})
test('dangerous, encoded and non-HTTP links never become anchors', async () => {
  for (const url of ['javascript:alert(1)', 'jav&#x61;script:alert(1)', 'data:text/html,evil', 'vbscript:evil', 'file:///secret', '//evil.example', '/relative', 'mailto:a@example.com']) {
    assert.doesNotMatch(await render(`[link](${url})`), /<a\b/, url)
  }
})
test('malformed Markdown and long content render without exceptions', async () => {
  for (const source of ['', '[broken](<', '**not closed', '`', '[source](https://example.com/' + 'x'.repeat(2000) + ')']) assert.equal(typeof await render(source), 'string')
})
test('only exact early-brief source type enables Markdown', async () => {
  assert.doesNotMatch(await render('**text**', '新能源行业早报 '), /<strong>/)
})
test('narrow-screen rules contain long URLs and preserve plain-news typography', async () => {
  const css = await readFile('src/components/NewsBody.vue', 'utf8')
  assert.match(css, /overflow-wrap: anywhere/)
  assert.match(css, /@media \(max-width: 600px\)/)
  assert.match(css, /font-size: 17px; line-height: 1.85/)
})
test('draft editor uses admin read and explicitly preserves publish state', async () => {
  const source = await readFile('src/views/NewsEditView.vue', 'utf8')
  assert.match(source, /\/api\/admin\/news\/\$\{encodeURIComponent\(id\)\}/)
  assert.match(source, /form.is_published = data.is_published === 1/)
  assert.match(source, /is_published: form.is_published \? 1 : 0/)
})

test('actual editor loads a draft via admin API and saves it unpublished', async () => {
  const { createMemoryHistory, createRouter } = await import('vue-router')
  const { default: Editor } = await server.ssrLoadModule('/src/views/NewsEditView.vue')
  const draft = { id: 7, title: 'Draft', summary: '', content: 'old', source: '', source_type: '行业资讯', publish_date: '2026-11-16', keywords: '', url: '', is_published: 0 }
  const originalFetch = globalThis.fetch
  const requests = []
  globalThis.fetch = async (url, options = {}) => {
    requests.push({ url, options })
    return { ok: true, status: 200, json: async () => ({ ...draft }) }
  }
  try {
    let bindings
    const Wrapped = { ...Editor, setup(props, context) { bindings = Editor.setup(props, context); return bindings } }
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/admin/news/:id/edit', component: Wrapped }] })
    await router.push('/admin/news/7/edit')
    await renderToString(createSSRApp(Wrapped).use(router))
    await bindings.loadNews('7')
    assert.equal(bindings.form.is_published, false)
    bindings.form.content = 'edited'
    await bindings.saveNews()
    const update = requests.find(r => r.options.method === 'PUT')
    assert.ok(requests.some(r => String(r.url).endsWith('/api/admin/news/7')))
    assert.equal(update.options.credentials, 'include')
    assert.equal(JSON.parse(update.options.body).is_published, 0)
    assert.equal(JSON.parse(update.options.body).content, 'edited')
  } finally {
    globalThis.fetch = originalFetch
  }
})
