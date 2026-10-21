import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import { createServer } from 'vite'
import { createSSRApp, computed, reactive, ref, shallowRef, nextTick } from 'vue'
import { renderToString } from '@vue/server-renderer'
import {
  createDiscovery,
  selectResources,
  validateExchangeFields,
  formatAddedDate,
  EXCHANGE_CROP,
  safeUrl,
} from '../src/utils/exchangeDiscovery.js'
import { createDemoResources } from '../src/data/exchangeDemo.js'
import { cropGeometry, exportSectionCrop } from '../src/utils/sectionImageCrop.js'

const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
})
after(() => server.close())
const { default: Card } = await server.ssrLoadModule('/src/components/exchange/ExchangeCard.vue')
const { default: SubmitForm } = await server.ssrLoadModule(
  '/src/components/exchange/ExchangeSubmitForm.vue',
)
const service = await server.ssrLoadModule('/src/services/exchange.js')

test('queue exactly matches the accepted prototype, including manual selection and round boundaries', async () => {
  const html = await readFile(
    new URL('../../artifacts/discovery-lab-v1.html', import.meta.url),
    'utf8',
  )
  const reference = vm.runInNewContext(
    `${html.slice(html.indexOf('function shuffle('), html.indexOf('function selectResources('))}; createDiscovery`,
  )
  const seeded = () => {
    let seed = 17
    return () => (seed = (seed * 16807) % 2147483647) / 2147483647
  }
  for (const count of [0, 1, 3, 8, 20]) {
    const ids = createDemoResources()
      .slice(0, count)
      .map((r) => r.id)
    const actual = createDiscovery(ids, null, seeded()),
      original = reference(ids, null, seeded())
    for (let i = 0; i < 100; i++) {
      if (i === 7 && ids.length)
        assert.equal(actual.select(ids.at(-1)), original.select(ids.at(-1)))
      assert.equal(actual.draw(), original.draw())
    }
    if (count > 1) {
      const queue = createDiscovery(ids)
      let last
      for (let round = 0; round < 4; round++) {
        const draws = ids.map(() => queue.draw())
        assert.equal(new Set(draws).size, count)
        assert.notEqual(draws[0], last)
        last = draws.at(-1)
      }
    }
  }
})

test('number, title and tag searches retain the unconsumed queue and fixed numbers', () => {
  const resources = createDemoResources()
  for (const query of ['25', '025', '巡检'])
    assert.equal(selectResources(resources, query)[0].id, 25)
  assert.ok(selectResources(resources, '自动化').length > 0)
  assert.deepEqual(selectResources(resources, '999999'), [])
  const queue = createDiscovery([1, 2, 25])
  queue.select(25)
  const remaining = [queue.draw(), queue.draw()]
  assert.deepEqual(new Set(remaining), new Set([1, 2]))
  assert.equal(resources.find((r) => r.id === 25).displayNumber, '025')
})

test('submission validation preserves content but never assigns a client ID or timestamp', () => {
  const fields = {
    title: '  新分享  ',
    description: '第一段\n\n第二段',
    reason: '原因',
    domain: '工作方法',
    type: '文章',
    tags: '效率，效率,方法',
    externalUrl: 'https://example.com/path',
  }
  const resource = validateExchangeFields(fields)
  assert.equal(resource.id, undefined)
  assert.equal(resource.displayNumber, undefined)
  assert.equal(resource.title, '新分享')
  assert.equal(resource.description, fields.description)
  assert.equal(resource.createdAt, undefined)
  assert.deepEqual(resource.tags, ['效率', '方法'])
  for (const changes of [
    { title: ' ' },
    { description: ' ' },
    { domain: 'invalid' },
    { type: 'invalid' },
    { externalUrl: 'javascript:alert(1)' },
    { title: 'x'.repeat(91) },
  ]) {
    assert.throws(() => validateExchangeFields({ ...fields, ...changes }))
  }
  assert.equal(safeUrl('data:text/html,test'), '')
})

test('resource card renders complete escaped content, safe links, date and no-cover archive without a detail dialog', async () => {
  const resource = {
    ...createDemoResources().find((r) => r.id === 25),
    title: '<img src=x onerror=alert(1)>',
    externalUrl: 'https://example.com/',
  }
  const html = await renderToString(createSSRApp(Card, { resource }))
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/)
  assert.ok(html.includes(resource.description))
  assert.match(html, /2026\.10\.07/)
  assert.match(html, /giant num/)
  assert.match(html, /class="archive-number num"[^>]*>025<\/span>/)
  assert.doesNotMatch(html, /RESOURCE ARCHIVE|匿名分享|archive-caption/)
  assert.match(html, /noopener noreferrer/)
  assert.doesNotMatch(html, /<dialog|关联|graph-|<img src=x/)
  const imageCard = await renderToString(
    createSSRApp(Card, { resource: { ...resource, imageUrl: 'blob:local-preview' } }),
  )
  assert.match(imageCard, /src="blob:local-preview"/)
  assert.doesNotMatch(imageCard, /giant num/)
  const invalidLink = await renderToString(
    createSSRApp(Card, { resource: { ...resource, externalUrl: 'javascript:alert(1)' } }),
  )
  assert.doesNotMatch(invalidLink, /resource-external/)
})

test('real form retains the safe-sharing reminder and has no mock persistence claims', async () => {
  const html = await renderToString(createSSRApp(SubmitForm, { open: false }))
  assert.match(html, /请勿上传公司敏感信息或未经授权公开的资料/)
  assert.match(html, /type="submit"/)
  assert.match(html, /推荐领域/)
  assert.match(html, /资源链接/)
  assert.doesNotMatch(html, /DISCOVERY LAB|CONNECTIONS|临时分享|刷新后消失|加入本页预览|匿名分享/)
})

test('real API adapter uses multipart, resolves persisted images, refreshes after deletion and reports failures', async () => {
  const previousFetch = globalThis.fetch
  const rows = [
    {
      ...createDemoResources()[0],
      createdAt: '2026-10-19T02:03:04.000Z',
      imageUrl: '/uploads/exchange/' + 'a'.repeat(32) + '.webp',
    },
  ]
  const calls = []
  globalThis.fetch = async (url, options = {}) => {
    calls.push([url, options])
    if (String(url).endsWith('/api/employee/csrf')) return new Response(JSON.stringify({ csrfToken: 'test-csrf-only' }))
    if (options.method === 'DELETE') {
      rows.splice(0)
      return new Response(JSON.stringify({ id: 1 }), { status: 200 })
    }
    if (options.method === 'POST') return new Response(JSON.stringify(rows[0]), { status: 201 })
    const result = String(url).includes('/api/admin/exchange')
      ? { items: [...rows], total: rows.length }
      : [...rows]
    return new Response(JSON.stringify(result), { status: 200 })
  }
  try {
    const initial = await service.loadExchangeResources()
    assert.equal(initial.length, 1)
    assert.match(initial[0].imageUrl, /\/uploads\/exchange\/a{32}\.webp$/)
    assert.equal(formatAddedDate(initial[0].createdAt), '2026.10.19')
    const fields = {
      title: '真实分享',
      description: '一句话',
      domain: '工作方法',
      type: '文章',
      imageBlob: new Blob(['crop'], { type: 'image/webp' }),
    }
    const saved = await service.submitExchangeResource(fields)
    assert.equal(saved.displayNumber, '001')
    const post = calls.find(([, options]) => options.method === 'POST')[1]
    assert.equal(post.headers.get('X-CSRF-Token'), 'test-csrf-only')
    assert.equal(post.headers.has('Content-Type'), false)
    assert.equal(post.body.get('file').type, 'image/webp')
    const payload = JSON.parse(post.body.get('payload'))
    assert.equal(payload.id, undefined)
    assert.equal(payload.createdAt, undefined)
    assert.equal(post.credentials, 'include')
    assert.equal((await service.loadAdminExchangeResources()).total, 1)
    await service.deleteExchangeResource(1)
    assert.equal(calls.find(([, options]) => options.method === 'DELETE')[1].credentials, 'include')
    assert.deepEqual(await service.loadExchangeResources(), [])
    for (const [status, detail] of [
      [400, '图片无法解码'],
      [413, '文件过大'],
      [422, '内容错误'],
      [429, '提交过于频繁'],
      [500, '服务器保存失败'],
      [503, '暂未开放'],
    ]) {
      globalThis.fetch = async () => new Response(JSON.stringify({ detail }), { status })
      await assert.rejects(
        service.submitExchangeResource(fields),
        (error) => error.status === status && error.message === detail,
      )
    }
    globalThis.fetch = async () => {
      throw new TypeError('offline')
    }
    await assert.rejects(service.loadExchangeResources(), /网络连接失败/)
  } finally {
    globalThis.fetch = previousFetch
  }
})

test('11:10 shared crop geometry and Canvas output use exactly the same source rectangle', async () => {
  const previousDocument = globalThis.document
  let drawArgs
  const canvas = {
    getContext: () => ({
      drawImage: (...args) => {
        drawArgs = args
      },
    }),
    toBlob: (callback, type, quality) => {
      assert.equal(type, 'image/webp')
      assert.equal(quality, 0.82)
      callback(new Blob(['crop'], { type }))
    },
  }
  globalThis.document = { createElement: () => canvas }
  try {
    for (const [w, h] of [
      [4000, 2000],
      [2000, 4000],
      [2000, 2000],
    ]) {
      for (const zoom of [1, 2, 4]) {
        const g = cropGeometry(w, h, EXCHANGE_CROP.width, EXCHANGE_CROP.height, zoom, 99999, -99999)
        assert.ok(g.sourceX >= 0 && g.sourceY >= 0)
        assert.ok(g.sourceX + g.sourceWidth <= w + 1e-8)
        assert.ok(g.sourceY + g.sourceHeight <= h + 1e-8)
        assert.ok(Math.abs(g.sourceWidth / g.sourceHeight - 11 / 10) < 1e-8)
        const image = {}
        await exportSectionCrop(image, g, EXCHANGE_CROP.outputWidth, EXCHANGE_CROP.outputHeight)
        assert.equal(canvas.width, 1320)
        assert.equal(canvas.height, 1200)
        assert.deepEqual(drawArgs, [
          image,
          g.sourceX,
          g.sourceY,
          g.sourceWidth,
          g.sourceHeight,
          0,
          0,
          1320,
          1200,
        ])
      }
    }
  } finally {
    if (previousDocument === undefined) delete globalThis.document
    else globalThis.document = previousDocument
  }
})

async function scriptHarness(relativePath, bindings = {}) {
  const source = await readFile(new URL(relativePath, import.meta.url), 'utf8')
  const script = source
    .match(/<script setup>([\s\S]*?)<\/script>/)[1]
    .replace(/^import\s[\s\S]*?\sfrom\s+['"][^'"]+['"];?\s*$/gm, '')
    .replace(/^import\s+['"][^'"]+['"];?\s*$/gm, '')
  const events = [],
    cleanup = []
  const context = vm.createContext({
    computed,
    reactive,
    ref,
    shallowRef,
    nextTick,
    URL,
    Blob,
    watch: () => {},
    onMounted: () => {},
    onBeforeUnmount: (fn) => cleanup.push(fn),
    defineProps: () => ({ open: true }),
    defineEmits: () => (name, value) => events.push([name, value]),
    EXCHANGE_CROP,
    EXCHANGE_DOMAINS: ['工作方法'],
    EXCHANGE_TYPES: ['文章'],
    ...bindings,
  })
  vm.runInContext(script, context)
  return { run: (code) => vm.runInContext(code, context), events, cleanup }
}

test('share form retains the crop on failure, prevents duplicate posts, then signals only confirmed server success', async () => {
  let calls = 0,
    release,
    fail = true
  const saved = { ...createDemoResources()[0], id: 1001, displayNumber: '1001' }
  const harness = await scriptHarness('../src/components/exchange/ExchangeSubmitForm.vue', {
    submitExchangeResource: async (fields) => {
      calls++
      assert.equal(fields.imageBlob.type, 'image/webp')
      if (fail) throw new Error('服务器保存失败')
      return new Promise((resolve) => {
        release = () => resolve(saved)
      })
    },
  })
  await harness.run("confirmCrop(new Blob(['preview'], {type:'image/webp'}))")
  const oldUrl = harness.run('previewUrl.value')
  await harness.run('cancelCrop()')
  assert.equal(harness.run('previewUrl.value'), oldUrl)
  await harness.run('submit()')
  assert.equal(harness.events.length, 0)
  assert.match(harness.run('errorMessage.value'), /保存失败/)
  assert.equal(harness.run('previewUrl.value'), oldUrl)
  fail = false
  const pending = harness.run('submit()')
  await harness.run('submit()')
  assert.equal(calls, 2)
  assert.equal(harness.run('submitting.value'), true)
  release()
  await pending
  assert.equal(harness.events[0][0], 'submitted')
  assert.equal(harness.events[0][1].id, 1001)
  assert.equal(harness.run('successMessage.value'), '分享成功 · 1001')
  for (const cleanup of harness.cleanup) cleanup()
})

test('admin view requires confirmation, reads full detail and refreshes the real list after deletion', async () => {
  const rows = createDemoResources().slice(0, 2)
  let confirmed = false,
    deletes = 0
  const harness = await scriptHarness('../src/views/ExchangeAdminView.vue', {
    window: { confirm: () => confirmed },
    formatExchangeTimestamp: () => '',
    safeUrl,
    loadAdminExchangeResources: async () => ({ items: [...rows], total: rows.length }),
    loadAdminExchangeDetail: async (id) => rows.find((r) => r.id === id),
    deleteExchangeResource: async (id) => {
      deletes++
      rows.splice(
        rows.findIndex((r) => r.id === id),
        1,
      )
      return { id }
    },
  })
  await harness.run('refresh()')
  await harness.run('viewDetail(items.value[0])')
  assert.equal(harness.run('selected.value.id'), 1)
  await harness.run('remove(selected.value)')
  assert.equal(deletes, 0)
  confirmed = true
  await harness.run('remove(selected.value)')
  assert.equal(deletes, 1)
  assert.equal(harness.run('selected.value'), null)
  assert.equal(harness.run('items.value.length'), 1)
  assert.match(harness.run('successMessage.value'), /001 号分享已删除/)
})
