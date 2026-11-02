import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { createServer } from 'vite'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createMemoryHistory, createRouter } from 'vue-router'

// Compile the actual Vue components without listening on a server port.
const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
after(() => server.close())
const { default: Masthead } = await server.ssrLoadModule('/src/components/SectionMasthead.vue')
const { default: Chevron } = await server.ssrLoadModule('/src/components/ChevronRight.vue')
const { default: ToolGrid } = await server.ssrLoadModule('/src/components/ToolGrid.vue')
const { default: ToolForm } = await server.ssrLoadModule('/src/views/ToolFormView.vue')
const { default: Cropper } = await server.ssrLoadModule('/src/components/SectionImageCropper.vue')

for (const [title, to, navigationAriaLabel] of [
  ['最新动态', '/news', '查看全部新闻'], ['AI 与常用工具', '/tools', '查看全部工具'],
]) {
  for (const textMode of ['dark', 'light']) {
    test(`${title}: ${textMode} uses one semantic link and shared chevron`, async () => {
      const router = createRouter({ history: createMemoryHistory(), routes: [{ path: to, component: { template: '<div />' } }] })
      await router.push(to)
      const app = createSSRApp(Masthead, { title, to, navigationLabel: '全部', navigationAriaLabel, textMode, image: '/test.webp' })
      app.use(router)
      const html = await renderToString(app)
      assert.equal((html.match(/<a\s/g) || []).length, 1)
      assert.ok(html.includes(`href="${to}"`))
      assert.doesNotMatch(html, /<span\b[^>]*>全部<\/span>/)
      assert.match(html, /class="masthead-navigation"[^>]*aria-hidden="true"/)
      assert.match(html, /<svg\b[^>]*width="28"[^>]*height="28"[^>]*stroke-width="3"/)
      assert.ok(html.includes(`aria-label="${navigationAriaLabel}"`))
      assert.ok(html.includes('m9 6 6 6-6 6'))
      assert.equal(html.includes('is-light'), textMode === 'light')
      assert.ok(!html.includes('<button'))
    })
  }
}

test('admin preview uses the same component without an interactive link', async () => {
  const html = await renderToString(createSSRApp(Masthead, {
    title: '最新动态', to: '/news', navigationLabel: '全部', preview: true, textMode: 'light',
  }))
  assert.ok(html.includes('is-preview'))
  assert.ok(html.includes('is-light'))
  assert.doesNotMatch(html, /<span\b[^>]*>全部<\/span>/)
  assert.match(html, /<svg\b[^>]*width="28"[^>]*height="28"[^>]*stroke-width="3"/)
  assert.ok(!html.includes('<a '))
})

test('shared chevrons mirror geometry without changing viewBox, stroke or centring', async () => {
  const right = await renderToString(createSSRApp(Chevron))
  const left = await renderToString(createSSRApp(Chevron, { direction: 'left', size: 16 }))
  for (const html of [right, left]) {
    assert.match(html, /viewbox="0 0 24 24"/i)
    assert.ok(html.includes('stroke="currentColor"'))
    assert.ok(html.includes('stroke-width="2"'))
    assert.ok(html.includes('stroke-linecap="round"'))
    assert.ok(html.includes('aria-hidden="true"'))
  }
  assert.ok(right.includes('width="18"'))
  assert.ok(right.includes('m9 6 6 6-6 6'))
  assert.ok(left.includes('width="16"'))
  assert.ok(left.includes('m15 6-6 6 6 6'))
})

// Seed only the actual component's in-memory refs for SSR. onMounted API loading
// remains unchanged; no fixtures enter production props, APIs or the database.
const toolFixtures = [
  { id: 1, title: 'Route tool', status: 'available', actionType: 'route', actionTarget: '/news' },
  { id: 2, title: 'Developing tool', status: 'developing', actionType: 'external', actionTarget: 'https://example.org/' },
  { id: 3, title: 'Static tool', status: 'available', actionType: 'static', actionTarget: '/tools/qstart/index.html' },
  { id: 4, title: 'External tool', status: 'available', actionType: 'external', actionTarget: 'https://example.org/' },
  { id: 5, title: 'Later tool', status: 'available', actionType: 'route', actionTarget: '/tools' },
  { id: 6, title: 'Integrating tool', status: 'integrating', actionType: 'none', actionTarget: '' },
].map((tool) => ({ ...tool, icon: 'TEST', description: 'Sample description', buttonText: 'Open' }))

async function renderToolCards(home, fixtures = toolFixtures, extraProps = {}, failedBackgrounds = {}) {
  const SeededGrid = {
    ...ToolGrid,
    setup(props, context) {
      const bindings = ToolGrid.setup(props, context)
      bindings.tools.value = fixtures
      bindings.loading.value = false
      bindings.failedBackgrounds.value = failedBackgrounds
      return bindings
    },
  }
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/tools', component: { template: '<div />' } },
    { path: '/news', component: { template: '<div />' } },
  ] })
  await router.push('/tools')
  return renderToString(createSSRApp(SeededGrid, { home, detailed: !home, ...extraProps }).use(router))
}

test('home tools keep API order, show four, and have one valid entry per available card', async () => {
  const html = await renderToolCards(true)
  assert.equal((html.match(/<(?:a|article)\b[^>]*class="tool-card\b/g) || []).length, 4)
  assert.ok(html.indexOf('Route tool') < html.indexOf('Developing tool'))
  assert.ok(html.indexOf('Developing tool') < html.indexOf('Static tool'))
  assert.ok(html.indexOf('Static tool') < html.indexOf('External tool'))
  assert.ok(!html.includes('Later tool'))
  assert.equal((html.match(/启动/g) || []).length, 3)
  assert.equal((html.match(/敬请期待/g) || []).length, 1)
  assert.equal((html.match(/class="tool-home-action-label"/g) || []).length, 3)
  assert.match(html, /class="tool-home-action-label"[^>]*>启动<\/span><svg\b[^>]*width="18"[^>]*height="18"/)
  const unavailable = html.match(/<article\b[^>]*aria-disabled="true"[\s\S]*?<\/article>/)?.[0] || ''
  assert.ok(!unavailable.includes('tool-home-action-label'))
  assert.ok(!unavailable.includes('tool-surface-arrow'))
  assert.ok(!html.includes('class="tool-status'))
  assert.ok(!html.includes('class="tool-icon'))
  assert.ok(!html.includes('class="tool-action'))
  assert.ok(!html.includes('tool-card--featured'))
  assert.match(html, /<article\b[^>]*aria-disabled="true"/)
  assert.equal((html.match(/target="_blank"/g) || []).length, 2)
  assert.equal((html.match(/rel="noopener noreferrer"/g) || []).length, 2)
  assert.ok(html.includes('href="/tools/qstart/index.html"'))
})

test('home tools never manufacture cards when fewer than four are returned', async () => {
  const html = await renderToolCards(true, toolFixtures.slice(0, 2))
  assert.equal((html.match(/<(?:a|article)\b[^>]*class="tool-card\b/g) || []).length, 2)
})

test('home images stay mapped by ID and failed images fall back without losing entries', async () => {
  const backgrounds = { 1: '/test/first.webp', 3: '/test/third.webp' }
  const html = await renderToolCards(true, toolFixtures, { backgroundImages: backgrounds })
  assert.equal((html.match(/<img\b/g) || []).length, 2)
  assert.match(html, /class="tool-background"[^>]*src="\/test\/first.webp"/)
  assert.match(html, /\balt(?:="")?\s+aria-hidden="true"/)
  assert.ok(html.indexOf('/test/first.webp') < html.indexOf('>Route tool</h3>'))
  assert.equal((html.match(/data-background-state="unconfigured"/g) || []).length, 2)
  const failed = await renderToolCards(true, toolFixtures, { backgroundImages: backgrounds }, { 1: backgrounds[1] })
  assert.equal((failed.match(/<img\b/g) || []).length, 1)
  assert.ok(!failed.includes('/test/first.webp'))
  assert.ok(failed.includes('Route tool'))
  assert.ok(failed.includes('href="/news"'))
  assert.equal((failed.match(/data-background-state="error"/g) || []).length, 1)
  assert.equal((failed.match(/data-background-state="unconfigured"/g) || []).length, 2)
})

test('development preview fills two cards without replacing an explicit ID mapping', async () => {
  const html = await renderToolCards(true, toolFixtures, {
    developmentPreviewImages: ['/preview/first.png', '/preview/second.png'],
    backgroundImages: { 1: '/configured/first.webp' },
  })
  assert.ok(html.includes('tool-preview-notice'))
  assert.ok(html.includes('/configured/first.webp'))
  assert.ok(html.includes('/preview/second.png'))
  assert.ok(!html.includes('/preview/first.png'))
  assert.equal((html.match(/<img\b/g) || []).length, 2)
  assert.equal((html.match(/data-background-state="unconfigured"/g) || []).length, 2)
  assert.ok(html.includes('href="/news"'))
})

test('persisted tool cover takes precedence over local and development images', async () => {
  const html = await renderToolCards(true, [{ ...toolFixtures[0], coverImageUrl: '/uploads/tools/saved.webp' }], {
    backgroundImages: { 1: '/local.webp' }, developmentPreviewImages: ['/preview.webp'],
  })
  assert.ok(html.includes('/uploads/tools/saved.webp'))
  assert.ok(!html.includes('/local.webp'))
  assert.ok(!html.includes('/preview.webp'))
})

test('card preview uses real home markup without a link, masthead or data fetch', async () => {
  const tool = { ...toolFixtures[0], title: 'QsTArT 站点信息快速导入工具', description: '完整说明\n保留原文' }
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/news', component: { template: '<div />' } }] })
  await router.push('/news')
  const html = await renderToString(createSSRApp(ToolGrid, { home: true, previewTool: tool, backgroundImages: { 1: 'blob:test-image' } }).use(router))
  assert.ok(html.includes('section--preview'))
  assert.ok(html.includes('tool-home-copy'))
  assert.ok(html.includes('QsTArT 站点信息快速导入工具'))
  assert.ok(html.includes('完整说明\n保留原文'))
  assert.ok(html.includes('blob:test-image'))
  assert.ok(html.includes('启动'))
  assert.ok(!html.includes('<a '))
  assert.ok(!html.includes('section-masthead'))
})

async function mountNewToolForm() {
  let bindings
  const Wrapped = { ...ToolForm, setup(props, context) { bindings = ToolForm.setup(props, context); return bindings } }
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/admin/tools/new', component: { template: '<div />' } },
    { path: '/admin/tools', component: { template: '<div />' } },
  ] })
  await router.push('/admin/tools/new')
  const app = createSSRApp(Wrapped).use(router)
  const html = await renderToString(app)
  return { bindings, html }
}

test('tool editor removes icon input and retains full original text in its payload', async () => {
  const { bindings, html } = await mountNewToolForm()
  assert.ok(!html.includes('form.icon'))
  assert.ok(!html.includes('图标'))
  assert.ok(html.includes('首页卡片预览'))
  assert.ok(html.includes('2:1'))
  bindings.form.title = '完整工具名称'
  bindings.form.description = '  第一行\n第二行完整说明  '
  assert.equal(bindings.buildPayload().description, '  第一行\n第二行完整说明  ')
  assert.equal(bindings.previewTool.value.title, '完整工具名称')
  assert.ok(!('icon' in bindings.buildPayload()))
})

test('confirmed tool image stays local until one multipart save and survives errors', async () => {
  const { bindings } = await mountNewToolForm()
  bindings.form.title = '工具草稿'
  bindings.savedImage.value = '/uploads/tools/old.webp'
  const blob = new Blob(['cropped'], { type: 'image/webp' })
  const previousFetch = globalThis.fetch
  let requests = 0
  try {
    bindings.confirmImage(blob)
    assert.equal(bindings.pendingImage.value, blob)
    assert.equal(bindings.savedImage.value, '/uploads/tools/old.webp')
    assert.ok(bindings.previewImage.value.startsWith('blob:'))
    globalThis.fetch = async (url, init) => {
      requests++
      assert.ok(String(url).endsWith('/api/admin/tools'))
      assert.equal(init.method, 'POST')
      assert.equal(init.credentials, 'include')
      assert.equal(init.headers, undefined)
      assert.ok(init.body instanceof FormData)
      assert.equal(init.body.get('file').type, 'image/webp')
      const payload = JSON.parse(init.body.get('payload'))
      assert.equal(payload.title, '工具草稿')
      assert.equal(payload.removeImage, false)
      return new Response(JSON.stringify({ detail: '模拟图片保存失败' }), { status: 400 })
    }
    await bindings.submitTool()
    assert.equal(requests, 1)
    assert.equal(bindings.savedImage.value, '/uploads/tools/old.webp')
    assert.equal(bindings.pendingImage.value, blob)
    assert.equal(bindings.successMessage.value, '')
    assert.equal(bindings.errorMessage.value, '模拟图片保存失败')
    globalThis.fetch = async () => new Response(JSON.stringify({
      id: 9, title: '工具草稿', status: 'available', actionType: 'none', isActive: 1,
      coverImageUrl: '/uploads/tools/new.webp',
    }))
    await bindings.submitTool()
    assert.equal(bindings.savedImage.value, '/uploads/tools/new.webp')
    assert.equal(bindings.pendingImage.value, null)
    assert.equal(bindings.hasChanges.value, false)
    assert.equal(bindings.createdId.value, 9)
    assert.ok(bindings.successMessage.value)
  } finally {
    bindings.releasePending()
    globalThis.fetch = previousFetch
  }
})

test('discarding a draft or pending removal keeps the effective tool cover', async () => {
  const { bindings } = await mountNewToolForm()
  bindings.savedImage.value = '/uploads/tools/effective.webp'
  bindings.form.title = '未保存名称'
  bindings.confirmImage(new Blob(['draft'], { type: 'image/webp' }))
  bindings.clearImage()
  assert.equal(bindings.previewImage.value, '')
  assert.equal(bindings.savedImage.value, '/uploads/tools/effective.webp')
  assert.equal(bindings.removeImage.value, true)
  bindings.discardChanges()
  assert.equal(bindings.pendingImage.value, null)
  assert.equal(bindings.removeImage.value, false)
  assert.ok(bindings.previewImage.value.endsWith('/uploads/tools/effective.webp'))
  assert.equal(bindings.form.title, '')
})

test('local crop confirmation exports WebP but cannot call the section save API', async () => {
  let bindings, confirmed
  const Wrapped = { ...Cropper, setup(props, context) { bindings = Cropper.setup(props, context); return bindings } }
  await renderToString(createSSRApp(Wrapped, {
    localOnly: true,
    section: { key: 'tool-cover', title: '工具图片', width: 600, height: 300, outputWidth: 1600, outputHeight: 800 },
    onConfirmed: blob => { confirmed = blob },
  }))
  const previousDocument = globalThis.document
  const previousFetch = globalThis.fetch
  const result = new Blob(['webp'], { type: 'image/webp' })
  globalThis.document = { createElement: () => ({
    getContext: () => ({ drawImage: () => {} }),
    toBlob: (callback, type, quality) => { assert.equal(type, 'image/webp'); assert.equal(quality, 0.82); callback(result) },
  }) }
  globalThis.fetch = () => { throw new Error('Local crop must not upload') }
  try {
    bindings.image.value = { naturalWidth: 1200, naturalHeight: 600 }
    await bindings.confirmCrop()
    assert.equal(confirmed, result)
    assert.equal(bindings.phase.value, 'ready')
    await bindings.save()
    assert.equal(bindings.errorMessage.value, '')
  } finally {
    bindings.releaseResult()
    globalThis.document = previousDocument
    globalThis.fetch = previousFetch
  }
})

test('featured IDs are explicit and never make an unavailable tool interactive', async () => {
  const html = await renderToolCards(true, toolFixtures, { featuredToolIds: [2] })
  assert.equal((html.match(/tool-card--featured/g) || []).length, 1)
  assert.match(html, /<article\b[^>]*class="[^"]*tool-card--featured[^>]*aria-disabled="true"/)
  assert.equal((html.match(/启动/g) || []).length, 3)
  assert.equal((html.match(/敬请期待/g) || []).length, 1)
})

test('detailed tools keep the complete list, icons, status and existing actions', async () => {
  const html = await renderToolCards(false, toolFixtures, {
    featuredToolIds: [1], backgroundImages: { 1: '/test/first.webp' },
  })
  assert.equal((html.match(/<article\b[^>]*class="tool-card\b/g) || []).length, 6)
  assert.ok(html.includes('Later tool'))
  assert.ok(html.includes('Integrating tool'))
  assert.ok(html.includes('class="tool-icon'))
  assert.ok(html.includes('class="tool-status'))
  assert.ok(html.includes('class="tool-action'))
  assert.ok(!html.includes('tool-home-content'))
  assert.ok(!html.includes('启动'))
  assert.ok(!html.includes('tool-background'))
  assert.ok(!html.includes('tool-card--featured'))
  assert.ok(!html.includes('tool-home-action-label'))
})
