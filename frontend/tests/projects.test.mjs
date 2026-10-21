import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { setImmediate as nextTurn } from 'node:timers/promises'
import { createServer } from 'vite'
import { createSSRApp, computed, nextTick, reactive, ref } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { displayValue, importTime, scaleValue, stageTone } from '../src/utils/projectDisplay.js'

const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
})
after(() => server.close())
const { default: Dashboard } = await server.ssrLoadModule('/src/components/ProjectDashboard.vue')
const { default: Detail } = await server.ssrLoadModule('/src/components/ProjectDetail.vue')
const { default: View } = await server.ssrLoadModule('/src/views/ProjectsAdminView.vue')
const service = await server.ssrLoadModule('/src/services/projects.js')
const stages = [
  '客户对接',
  '实地勘察',
  '资料收集与方案设计',
  '商务洽谈',
  '可研编制',
  '项目审批',
  '合同签约',
  '项目备案',
  '招标',
  '施工',
  '竣工投运',
]
const project = {
  id: 1,
  name: 'XX希尔顿酒店分布式光伏项目',
  owner: '负责人B',
  leader: '组长A',
  resource: '酒店',
  district: '南京市江宁区',
  priority: '甲：尽快推进',
  valueRating: 'A级',
  pvArea: '15000㎡',
  pvCapacity: '1.8MW',
  currentStage: '商务洽谈',
  situation: '管委会不同意建设光伏，理由还是影响酒店美观度，保持跟进。',
  nextStep: '关注央巡结束时间，完善合作方案，争取合作机会。',
  coordination: null,
  progressUpdate: '无',
  stages: ['已完成', '已完成', '已完成', '进行中', ...Array(7).fill(null)],
  completedCount: 3,
  needsCoordination: false,
  importedAt: '2026-10-19T12:00:00Z',
}
const dashboardData = (projects = [project]) => ({
  summary: { total: projects.length, priority: projects.length, coordination: 0, operational: 0 },
  distribution: [...stages, '未明确'].map((name) => ({
    name,
    count: name === '商务洽谈' ? projects.length : 0,
  })),
  projects,
  filteredCount: projects.length,
  coordination: [],
  districts: ['南京市江宁区'],
  stages,
  businessFields: [
    ['pvArea', '光伏可利用面积', '㎡'],
    ['pvCapacity', '光伏装机规模', 'MW'],
  ],
  latestImport: { importedAt: project.importedAt },
})
const filters = { search: '', stage: '', district: '', focus: '' }
const viewSource = await readFile(
  new URL('../src/views/ProjectsAdminView.vue', import.meta.url),
  'utf8',
)
const viewSetup = viewSource
  .match(/<script setup>([\s\S]*?)<\/script>/)[1]
  .replace(/^import[\s\S]*?['"][^'"]+['"]\s*(?:\r?\n|$)/gm, '')
  .replace(/onMounted\(refresh\)/, '')
  .replace(/onBeforeUnmount\(\(\) => \{[\s\S]*?\n\}\)/, '')
const viewFactory = new Function(
  'computed',
  'ref',
  'reactive',
  'nextTick',
  'loadProjects',
  'confirmProjects',
  'cancelProjectPreview',
  'loadProjectDetail',
  'previewProjects',
  'displayValue',
  `${viewSetup}; return { preview, importBusy, importDialog, importError, success, confirmImport, chooseFile, refresh, filter, filters, data, loading, error, closeImport };`,
)
const createViewState = (overrides = {}) =>
  viewFactory(
    computed,
    ref,
    reactive,
    nextTick,
    overrides.load || (async () => dashboardData()),
    overrides.confirm || (async () => ({})),
    overrides.cancel || (async () => ({})),
    async () => project,
    overrides.preview || (async () => ({})),
    displayValue,
  )

test('real dashboard renders server statistics, all stage buckets and full card summaries without completion percentages', async () => {
  const html = await renderToString(createSSRApp(Dashboard, { data: dashboardData(), filters }))
  assert.match(html, /项目推进/)
  assert.match(html, /XX希尔顿酒店分布式光伏项目/)
  assert.match(html, /甲：尽快推进/)
  assert.match(html, /A级/)
  assert.match(html, /南京市江宁区/)
  assert.match(html, /已完成 3 \/ 11 节点/)
  assert.match(html, /关注央巡结束时间/)
  assert.equal((html.match(/class="stage-chart-label"/g) || []).length, 12)
  assert.equal((html.match(/title="\d+\./g) || []).length, 11)
  assert.doesNotMatch(html, /27%|延期|风险等级/)
})

test('empty, filtered empty and loading states remain meaningful and do not seed demo numbers', async () => {
  const empty = dashboardData([])
  empty.latestImport = null
  const html = await renderToString(createSSRApp(Dashboard, { data: empty, filters }))
  assert.match(html, /从一份台账，开始看清项目全貌/)
  assert.match(html, /尚未导入/)
  assert.doesNotMatch(html, /希尔顿/)
  const filtered = await renderToString(
    createSSRApp(Dashboard, {
      data: { ...empty, summary: { ...empty.summary, total: 1 } },
      filters: { ...filters, search: '无结果' },
    }),
  )
  assert.match(filtered, /没有符合筛选条件的项目/)
  const busy = await renderToString(
    createSSRApp(Dashboard, { data: empty, filters, loading: true }),
  )
  assert.match(busy, /正在读取项目台账/)
  assert.match(busy, /aria-busy="true"/)
})

test('details retain full escaped long text and unknown states, preserve scales and AG raw text', async () => {
  const longText = '<script>alert(1)</script>\n完整情况  '.repeat(100)
  const detail = {
    ...project,
    situation: longText,
    stages: [...project.stages.slice(0, 10), '待核实'],
    coordination: '请协调\n保留第二行',
  }
  const html = await renderToString(
    createSSRApp(Detail, {
      project: detail,
      names: stages,
      businessFields: dashboardData().businessFields,
    }),
  )
  assert.match(html, /15000㎡/)
  assert.match(html, /1.8MW/)
  assert.match(html, /待核实/)
  assert.match(html, /是否有进度更新（台账原值）/)
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/)
  assert.equal((html.match(/完整情况/g) || []).length, 100)
  assert.match(html, /请协调\n保留第二行/)
  assert.equal((html.match(/timeline-marker/g) || []).length, 11)
  assert.doesNotMatch(html, /27%|延期天数/)
})

test('unknown, completed, active and blank stages have separate semantics; dates always use China time', () => {
  assert.equal(stageTone(null), 'blank')
  assert.equal(stageTone('已完成'), 'done')
  assert.equal(stageTone('进行中'), 'active')
  assert.equal(stageTone('待确认'), 'other')
  assert.equal(displayValue(null), '未填写')
  assert.equal(scaleValue(null, 'MW'), '未填写')
  assert.equal(scaleValue('1.8', 'MW'), '1.8 MW')
  assert.equal(scaleValue('1.8MW', 'MW'), '1.8MW')
  assert.match(importTime('2026-10-19T12:00:00Z'), /20:00/)
})

test('API adapter sends authenticated multipart, filters and token-only confirmation; HTTP errors stay visible', async () => {
  const original = globalThis.fetch
  const requests = []
  globalThis.fetch = async (url, init) => {
    if (String(url).endsWith('/api/employee/csrf')) return new Response(JSON.stringify({ csrfToken: 'projects-test-csrf' }))
    requests.push({ url, init })
    return { ok: true, json: async () => ({ ok: true }) }
  }
  try {
    await service.loadProjects({
      search: '酒店',
      stage: '商务洽谈',
      focus: 'priority',
      district: '',
    })
    const file = new File(['fixture-only'], '台账.xlsx')
    await service.previewProjects(file)
    await service.confirmProjects('server-issued-token')
    await service.cancelProjectPreview('server-issued-token')
    assert.ok(requests.every(({ init }) => init.credentials === 'include'))
    assert.match(requests[0].url, /search=/)
    assert.equal(new URL(requests[0].url, 'http://localhost').searchParams.get('stage'), '商务洽谈')
    assert.ok(requests[1].init.body instanceof FormData)
    assert.equal(requests[1].init.body.get('file').name, '台账.xlsx')
    assert.deepEqual(JSON.parse(requests[2].init.body), { token: 'server-issued-token' })
    assert.equal(requests[3].init.method, 'DELETE')
    globalThis.fetch = async () => ({
      ok: false,
      status: 409,
      json: async () => ({ detail: '台账已发生变化' }),
    })
    await assert.rejects(service.confirmProjects('stale'), /台账已发生变化/)
  } finally {
    globalThis.fetch = original
  }
})

// Exercise the actual view's setup functions with an isolated service boundary,
// consistent with the existing component tests. No runtime feature flags or seeds.
function bindings(overrides = {}) {
  const Component = {
    ...View,
    setup(props, context) {
      const state = View.setup(props, context)
      Object.assign(state, overrides)
      return state
    },
  }
  return Component
}

test('view renders real accessible native dialogs, labels and disabled confirmation before preview', async () => {
  const html = await renderToString(createSSRApp(bindings()))
  assert.match(html, /aria-labelledby="project-import-title"/)
  assert.match(html, /aria-label="选择项目 Excel 台账"/)
  assert.match(html, /type="file"/)
  assert.match(html, /disabled[^>]*>\s*确认导入/)
  assert.match(html, /aria-labelledby="project-detail-title"/)
})

test('coordination section displays complete server-provided matters and selected filters are accessible', async () => {
  const data = dashboardData()
  data.coordination = [{ ...project, coordination: '请协调接入\n保留全部具体事项' }]
  const html = await renderToString(
    createSSRApp(Dashboard, {
      data,
      filters: { ...filters, stage: '商务洽谈', focus: 'coordination' },
    }),
  )
  assert.match(html, /请协调接入\n保留全部具体事项/)
  assert.match(html, /aria-pressed="true"/)
  assert.match(html, /清除筛选/)
  assert.match(html, /需协调事项/)
})

test('import confirmation stays single-flight, preserves preview on failure and refreshes only on confirmed success', async () => {
  const originalFetch = globalThis.fetch
  let confirmations = 0
  let shouldFail = true
  let resolveConfirmation
  const confirm = () => {
    confirmations++
    return new Promise((resolve, reject) => {
      resolveConfirmation = () =>
        shouldFail
          ? reject(new Error('保存失败'))
          : resolve({ counts: { new: 1, updated: 0, unchanged: 0 } })
    })
  }
  try {
    const state = createViewState({ confirm })
    state.importDialog.value = { close() {} }
    state.preview.value = { canConfirm: true, token: 'server-token' }
    const first = state.confirmImport()
    await state.confirmImport()
    assert.equal(confirmations, 1)
    resolveConfirmation()
    await first
    assert.match(state.importError.value, /保存失败/)
    assert.equal(state.preview.value.token, 'server-token')
    assert.equal(state.importBusy.value, false)
    shouldFail = false
    const second = state.confirmImport()
    resolveConfirmation()
    await second
    assert.equal(state.preview.value, null)
    assert.match(state.success.value, /新增 1 项/)
    assert.equal(state.data.value.summary.total, 1)
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('file selection rejects oversized/type-invalid files before upload, displays parsed errors and cancels old preview', async () => {
  let calls = 0
  const cancelled = []
  const state = createViewState({
    preview: async () => {
      calls++
      return {
        token: null,
        canConfirm: false,
        errors: ['重复项目'],
        counts: {},
        rows: [],
        warnings: [],
      }
    },
    cancel: async (token) => {
      cancelled.push(token)
    },
  })
  state.preview.value = { token: 'old-token' }
  await state.chooseFile({ target: { files: [new File(['x'], 'wrong.xls')] } })
  assert.match(state.importError.value, /不超过 4 MB/)
  assert.deepEqual(cancelled, ['old-token'])
  assert.equal(calls, 0)
  await state.chooseFile({ target: { files: [{ name: 'large.xlsx', size: 5 * 1024 * 1024 }] } })
  assert.equal(calls, 0)
  await state.chooseFile({ target: { files: [new File(['fixture'], '台账.xlsx')] } })
  assert.equal(calls, 1)
  assert.equal(state.preview.value.canConfirm, false)
  assert.deepEqual(state.preview.value.errors, ['重复项目'])
  assert.equal(state.importBusy.value, false)
})

test('stale confirmation invalidates preview and never shows false success', async () => {
  const state = createViewState({
    confirm: async () => {
      const error = new Error('重新上传')
      error.status = 409
      throw error
    },
  })
  state.preview.value = { canConfirm: true, token: 'expired-token' }
  await state.confirmImport()
  assert.equal(state.preview.value, null)
  assert.equal(state.success.value, '')
  assert.match(state.importError.value, /重新上传/)
})

test('out-of-order filtered requests cannot replace the latest response; failures stay visible', async () => {
  const pending = []
  const state = createViewState({
    load: (filters) =>
      new Promise((resolve, reject) => {
        pending.push({ search: filters.search, resolve, reject })
      }),
  })
  state.filter('search', '旧请求')
  state.filter('search', '新请求')
  pending[1].resolve({ ...dashboardData(), filteredCount: 2 })
  await nextTurn()
  pending[0].resolve({ ...dashboardData(), filteredCount: 99 })
  await nextTurn()
  assert.equal(state.data.value.filteredCount, 2)
  const failed = state.refresh()
  pending[2].reject(new Error('服务器暂不可用'))
  await failed
  assert.match(state.error.value, /服务器暂不可用/)
  assert.equal(state.loading.value, false)
})
