import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { createServer } from 'vite'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

// Exercise the real router in Node, substituting only the browser history adapter.
const server = await createServer({
  server: { middlewareMode: true, hmr: false }, appType: 'custom',
  plugins: [{
    name: 'test-memory-history', enforce: 'pre',
    transform(code, id) {
      if (id.replaceAll('\\', '/').endsWith('/src/router/index.js')) {
        return code.replaceAll('createWebHistory', 'createMemoryHistory')
      }
    },
  }],
})
after(() => server.close())
const { default: router } = await server.ssrLoadModule('/src/router/index.js')

test('the actual route table retains every independent portal and administration module', () => {
  for (const path of ['/', '/news', '/news/1', '/tools', '/exchange', '/assistant', '/login',
    '/change-password', '/admin', '/admin/employees', '/admin/exchange', '/admin/news',
    '/admin/news/new', '/admin/news/1/edit', '/admin/content/banners',
    '/admin/content/banners/sections', '/admin/content/banners/new', '/admin/content/banners/1/edit',
    '/admin/content/announcements', '/admin/content/announcements/new',
    '/admin/content/announcements/1/edit', '/admin/tools', '/admin/tools/new', '/admin/tools/1/edit']) {
    assert.ok(router.resolve(path).matched.length, path)
  }
  const records = router.getRoutes()
  const names = records.map((route) => route.name).filter(Boolean)
  assert.equal(new Set(names).size, names.length)
  assert.ok(records.every((route) => !route.path.includes('projects')))
  for (const path of ['/projects', '/projects/new', '/projects/1/edit', '/admin/projects']) {
    assert.equal(router.resolve(path).matched.length, 0, path)
  }
})

test('the real home page still renders the independent personal timeline and workspace', async () => {
  const { default: Home } = await server.ssrLoadModule('/src/views/HomeView.vue')
  const html = await renderToString(createSSRApp(Home).use(router))
  assert.match(html, /planner-expand-panel/)
  assert.match(html, /home-workspace/)
  const { default: Panel } = await server.ssrLoadModule('/src/components/PlannerExpandPanel.vue')
  const expanded = await renderToString(createSSRApp(Panel).use(router))
  assert.match(expanded, /timeline-module/)
})
