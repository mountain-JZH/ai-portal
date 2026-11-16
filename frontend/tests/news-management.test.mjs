import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createServer } from 'vite'

const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' })
after(() => server.close())
const { default: Create } = await server.ssrLoadModule('/src/views/NewsCreateView.vue')
const { default: List } = await server.ssrLoadModule('/src/views/NewsView.vue')

async function mountBindings(Component, seed = () => {}) {
  let bindings
  const Wrapped = { ...Component, setup(props, context) { bindings = Component.setup(props, context); seed(bindings); return bindings } }
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:pathMatch(.*)*', component: Wrapped }] })
  await router.push('/admin/news/new')
  const app = createSSRApp(Wrapped).use(router)
  const html = await renderToString(app)
  return { bindings, html }
}

test('draft and explicit publish requests preserve the selected state', async () => {
  const original = globalThis.fetch
  const writes = []
  globalThis.fetch = async (url, options) => {
    const data = JSON.parse(options.body)
    writes.push(data)
    return { ok: true, json: async () => ({ ...data, id: 9 }) }
  }
  try {
    const { bindings } = await mountBindings(Create)
    assert.equal(bindings.form.is_published, true)
    bindings.form.source_type = '新能源行业早报'
    bindings.form.is_published = false // SSR does not run client change watchers
    assert.equal(bindings.form.is_published, false)
    bindings.form.title = '新能源行业早报｜2026-11-16'
    bindings.form.content = '## 今日速览'
    await bindings.submitNews()
    assert.equal(writes[0].is_published, 0)
    assert.equal(bindings.successMessage.value, '草稿保存成功')
    bindings.form.is_published = true
    await bindings.submitNews()
    assert.equal(writes[1].is_published, 1)
    assert.equal(bindings.successMessage.value, '新闻发布成功')
  } finally { globalThis.fetch = original }
})

test('explicit save-draft overrides normal-news immediate publish without mutating its choice', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async (url, options) => {
    const data = JSON.parse(options.body)
    assert.equal(data.is_published, 0)
    return { ok: true, json: async () => ({ ...data, id: 9 }) }
  }
  try {
    const { bindings } = await mountBindings(Create)
    bindings.form.title = '普通新闻'
    await bindings.submitNews(false)
    assert.equal(bindings.form.is_published, true)
    assert.equal(bindings.successMessage.value, '草稿保存成功')
  } finally { globalThis.fetch = original }
})

test('failed creation shows failure and does not claim a saved draft', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({ detail: '测试失败' }) })
  try {
    const { bindings } = await mountBindings(Create)
    bindings.form.title = '失败测试'
    await bindings.submitNews(false)
    assert.equal(bindings.successMessage.value, '')
    assert.equal(bindings.createdNewsId.value, null)
    assert.equal(bindings.errorMessage.value, '测试失败')
  } finally { globalThis.fetch = original }
})

test('all/brief/other filters keep descending dates and include empty historical types', async () => {
  const fixtures = [
    { id: 1, title: 'Older', date: '2026-11-14', source_type: '行业资讯' },
    { id: 2, title: 'Brief', date: '2026-11-16', source_type: '新能源行业早报' },
    { id: 3, title: 'Legacy', date: '2026-11-15', source_type: '' },
  ]
  const { bindings } = await mountBindings(List, b => { b.newsList.value = fixtures; b.loading.value = false })
  assert.deepEqual(bindings.filteredNews.value.map(n => n.id), [2, 3, 1])
  bindings.newsFilter.value = 'brief'
  assert.deepEqual(bindings.filteredNews.value.map(n => n.id), [2])
  bindings.newsFilter.value = 'other'
  assert.deepEqual(bindings.filteredNews.value.map(n => n.id), [3, 1])
  bindings.newsList.value = []
  assert.deepEqual(bindings.filteredNews.value, [])
})
