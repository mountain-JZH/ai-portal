import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { createServer } from 'vite'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createMemoryHistory, createRouter } from 'vue-router'

const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
after(() => server.close())
const { default: Header } = await server.ssrLoadModule('/src/components/AppHeader.vue')

async function renderHeader(path) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: ['/', '/news', '/news/:id', '/exchange', '/tools', '/assistant', '/admin'].map((path) => ({
      path, component: { template: '<div />' },
    })),
  })
  await router.push(path)
  return renderToString(createSSRApp(Header).use(router))
}

test('header exposes only available navigation in the agreed order', async () => {
  const html = await renderHeader('/')
  const nav = html.match(/<nav\b[\s\S]*?<\/nav>/)?.[0] || ''
  assert.deepEqual([...nav.matchAll(/href="([^"]+)"/g)].map((match) => match[1]), [
    '/', '/news', '/exchange', '/tools', '/admin',
  ])
  assert.doesNotMatch(html, /平台公告|brand-logo|\/projects/)
  assert.match(html, /AI <span\b[^>]*class="portal-word"[^>]*>PORTAL<\/span>/)
  assert.match(html, /aria-label="信息运维部智能助手平台，返回首页"/)
  assert.match(html, /nav-item-admin/)
})

test('editorial header keeps Chinese brand, navigation and English signature in order', async () => {
  const html = await renderHeader('/')
  const left = html.match(/<a\b[^>]*class="[^"]*\bbrand\b[^>]*>[\s\S]*?<\/a>/)?.[0] || ''
  assert.match(left, /<mark\b[^>]*>智能助手<\/mark>平台/)
  assert.doesNotMatch(left, /brand-subtitle|brand-logo/)
  const signature = html.match(/<a\b[^>]*class="[^"]*\bbrand-signature\b[^"]*"[^>]*>[\s\S]*?<\/a>/)?.[0] || ''
  assert.match(signature, /class="brand-wordmark"/)
  assert.match(signature, /class="brand-subtitle"[^>]*>信息运维部<\/span>/)
  assert.ok(html.indexOf(left) < html.indexOf('<nav'))
  assert.ok(html.indexOf('</nav>') < html.indexOf(signature))
})

for (const [path, target] of [['/', '/'], ['/news', '/news'], ['/news/123', '/news'], ['/exchange', '/exchange'], ['/tools', '/tools']]) {
  test(`${path} highlights only ${target} with an accessible current-page marker`, async () => {
    const html = await renderHeader(path)
    const links = [...html.matchAll(/<a\b[^>]*class="[^"]*nav-link[^>]*>/g)].map((match) => match[0])
    const active = links.filter((link) => /\bis-current\b/.test(link))
    assert.equal(active.length, 1)
    assert.ok(active[0].includes(`href="${target}"`))
    assert.match(active[0], /aria-current="page"/)
  })
}

test('assistant retains all navigation without falsely selecting home', async () => {
  const html = await renderHeader('/assistant')
  assert.doesNotMatch(html, /\bis-current\b|aria-current="page"/)
  assert.match(html, /href="\/admin"/)
})
