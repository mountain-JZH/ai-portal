import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { execFileSync } from 'node:child_process'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import { computed, createSSRApp, nextTick, reactive, ref } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { acquireModalPageLock } from '../src/utils/modalPageLock.js'
import {
  businessGroups,
  businessLabel,
  businessPresentation,
  currentPosition,
  metricValue,
} from '../src/utils/projectBoard.js'

const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
})
after(() => server.close())
const { default: Card } = await server.ssrLoadModule('/src/components/ProjectBoardCard.vue')
const { default: Detail } = await server.ssrLoadModule('/src/components/ProjectReadOnlyDetail.vue')
const { default: View } = await server.ssrLoadModule('/src/views/ProjectsView.vue')
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
  id: 123,
  name: '虚构测试项目',
  resource: '虚构资源来源',
  stages: ['已完成', null, null, null, null, null, '进行中', ...Array(4).fill(null)],
  completedCount: 1,
  currentStage: '合同签约',
  pvCapacity: '0.06699999999999999',
  storageCapacity: '尚不能确定',
  energyType: '虚构类型',
  energyScale: '完整方案'.repeat(150),
  businessTypes: ['光伏', '储能', '分布式能源'],
  situation: '完整推进情况'.repeat(90),
  progressUpdate: '是',
  updated: true,
}

const source = await readFile(new URL('../src/views/ProjectsView.vue', import.meta.url), 'utf8')
const setup = source
  .match(/<script setup>([\s\S]*?)<\/script>/)[1]
  .replace(/^import[\s\S]*?['"][^'"]+['"]\s*(?:\r?\n|$)/gm, '')
const factory = new Function(
  'computed',
  'ref',
  'reactive',
  'nextTick',
  'onMounted',
  'onBeforeUnmount',
  'loadEmployeeProjects',
  'loadEmployeeProjectDetail',
  'businessLabel',
  'acquireModalPageLock',
  `${setup};return { view, updateDays, overview, people, businesses, moreFilters, activeTags, data, loading, error, refresh, changeView, changeRole, choosePerson, toggleBusiness, reset, drawer, detail, detailLoading, detailError, showDetail, closeDetail, closed, backdrop };`,
)

test('V2.8 role pills remember each role, business cards toggle OR selections, and reset is scoped', async () => {
  const state = createState(async () => ({ projects: [], options: {}, summary: {}, stages }))
  state.overview.search = '保留总览条件'
  state.changeRole('leader')
  state.choosePerson('虚构组长')
  state.changeRole('owner')
  state.choosePerson('虚构负责人')
  state.changeRole('leader')
  assert.equal(state.people.person, '虚构组长')
  state.view.value = 'business'
  state.toggleBusiness('光伏')
  state.toggleBusiness('储能')
  assert.deepEqual([...state.businesses.value], ['光伏', '储能'])
  assert.deepEqual([...state.activeTags.value], ['分布式光伏', '储能'])
  state.toggleBusiness('光伏')
  assert.deepEqual([...state.businesses.value], ['储能'])
  state.reset()
  assert.equal(state.businesses.value.length, 0)
  assert.equal(state.overview.search, '保留总览条件')
})

test('V2.8 markup keeps tabs before KPI, yellow second metric, grouped filters and no stage-stat row', async () => {
  const html = await renderToString(createSSRApp(View))
  assert.ok(html.indexOf('class="tabs"') < html.indexOf('class="metrics"'))
  assert.match(html, /class="(?=[^"]*\bmetric\b)(?=[^"]*\bmetric-accent\b)[^"]*"/)
  assert.match(html, /class="(?=[^"]*\bviewtab\b)(?=[^"]*\bactive\b)[^"]*"/)
  assert.match(html, /class="heading"[^>]*><strong[^>]*>项目推进看板/)
  assert.match(html, /id="moreFilters"[^>]*hidden/)
  assert.match(html, /class="filterbar"/)
  assert.doesNotMatch(html, /pb-distribution|阶段分布/)
  for (const label of ['在库项目', '今日更新', '重点推进', '需协调项目'])
    assert.ok(html.includes(label))
  const css = await readFile(new URL('../src/assets/project-board.css', import.meta.url), 'utf8')
  assert.match(css, /max-width:\s*1620px/)
  assert.match(css, /minmax\(216px,\s*29%\) minmax\(365px,\s*43%\) minmax\(227px,\s*28%\)/)
  assert.match(css, /@media\s*\(max-width:\s*930px\)/)
  assert.match(css, /@media\s*\(max-width:\s*650px\)/)
})

test('business KPIs distinguish numbers, explicit units and complete mixed narratives', () => {
  const storage = businessPresentation({ storageCapacity: '0.12' }, businessGroups[1])
  assert.equal(storage.kpis[0].unit, '')
  const explicit = businessPresentation({ storageCapacity: '0.12MWh' }, businessGroups[1])
  assert.equal(explicit.kpis[0].unit, 'MWh')
  const narrative = '虚构方案：节能率约18%，年节约电费约12万元。\n' + '保留全部说明。'.repeat(70)
  const energy = businessPresentation({ energyScale: narrative }, businessGroups[3])
  assert.equal(energy.descriptions[0].value, narrative)
  assert.equal(energy.kpis.length, 2)
  assert.equal(businessLabel('光伏'), '分布式光伏')
})

test('D drawer switches all four real sections without losing source content', async () => {
  for (const id of ['overview', 'progress', 'business', 'updates']) {
    const Section = {
      ...Detail,
      setup(props, context) {
        const state = Detail.setup(props, context)
        state.tab.value = id
        return state
      },
    }
    const html = await renderToString(createSSRApp(Section, { project, stages }))
    assert.equal(html.includes('class="stageitems"'), id === 'overview' || id === 'progress')
    assert.equal(html.includes(project.situation), id === 'overview' || id === 'updates')
    assert.equal(html.includes(project.energyScale), id === 'overview' || id === 'business')
    assert.match(html, /项目概览/)
    assert.match(html, /实时情况/)
  }
})

test('eight synthetic SQLite/API records render complete B cards and D details, not just empty state', async () => {
  const root = fileURLToPath(new URL('../../', import.meta.url))
  const python =
    process.env.PROJECT_TEST_PYTHON ||
    fileURLToPath(
      new URL(
        process.platform === 'win32'
          ? '../../backend/.venv/Scripts/python.exe'
          : '../../backend/.venv/bin/python',
        import.meta.url,
      ),
    )
  const script = `import sys,json
sys.path.insert(0,'backend/tests')
sys.path.insert(0,'backend')
from test_projects import ProjectTests
from project_board_fixtures import synthetic_projects
ProjectTests.setUpClass()
try:
 t=ProjectTests('test_eight_invented_acceptance_scenarios_persist_and_read_all_details')
 t.setUp()
 t.import_projects(synthetic_projects())
 status,_,result=t.request('GET','/api/projects',admin=False)
 assert status==200
 print(json.dumps(result,ensure_ascii=True))
finally:
 ProjectTests.tearDownClass()
`
  const data = JSON.parse(
    execFileSync(python, ['-c', script], { cwd: root, encoding: 'utf8', timeout: 30000 }),
  )
  assert.equal(data.projects.length, 8)
  for (const record of data.projects) {
    for (const Component of [Card, Detail]) {
      const html = await renderToString(
        createSSRApp(Component, { project: record, stages: data.stages }),
      )
      assert.ok(html.includes(record.name))
      assert.ok(html.includes(record.situation))
      assert.ok(html.includes(record.resource))
      assert.match(html, /竣工投运/)
      for (const field of ['chargingScale', 'energyScale'])
        if (record[field]) assert.ok(html.replace(/<[^>]*>/g, '').includes(record[field]))
      assert.doesNotMatch(html, /0\.06699999999999999|7\.92E-2/)
    }
    const card = await renderToString(createSSRApp(Card, { project: record, stages: data.stages }))
    assert.equal((card.match(/class="timeline-unit"/g) || []).length, 11)
    assert.match(card, /class="detailsbtn"/)
    assert.equal((card.match(/class="businessblock"/g) || []).length, record.businessTypes.length)
    if (record.name.includes('不连续')) {
      assert.equal(record.completedCount, 1)
      assert.equal(
        (card.match(/class="(?=[^"]*\btimeline-rect\b)(?=[^"]*\bdone\b)[^"]*"/g) || []).length,
        1,
      )
      assert.match(card, /进行中/)
    }
  }
})
const createState = (load, detailLoader = async () => project, onUnmount = () => {}) =>
  factory(
    computed,
    ref,
    reactive,
    nextTick,
    () => {},
    onUnmount,
    load,
    detailLoader,
    businessLabel,
    acquireModalPageLock,
  )

async function withDrawerDOM(run) {
  const previousDocument = globalThis.document
  const previousWindow = globalThis.window
  const style = (initial = {}) => {
    const entries = new Map(Object.entries(initial).map(([name, value]) => [name, [value, '']]))
    return {
      getPropertyValue: (name) => entries.get(name)?.[0] || '',
      getPropertyPriority: (name) => entries.get(name)?.[1] || '',
      setProperty: (name, value, priority = '') => entries.set(name, [value, priority]),
      removeProperty: (name) => entries.delete(name),
      snapshot: () => [...entries].sort(([a], [b]) => a.localeCompare(b)),
    }
  }
  const html = { style: style({ 'overflow-y': 'scroll', 'scroll-behavior': 'smooth' }) }
  html.style.setProperty('overflow-y', 'scroll', 'important')
  const body = {
    style: style({ width: '100%' }),
    getBoundingClientRect: () => ({ top: -430, left: -12, width: 1000 }),
  }
  const before = { html: html.style.snapshot(), body: body.style.snapshot() }
  const restored = [],
    focused = [],
    closeFocused = []
  const trigger = { isConnected: true, focus: (options) => focused.push(options) }
  const closeButton = { focus: (options) => closeFocused.push(options) }
  const doc = { documentElement: html, body, activeElement: trigger }
  const browser = {
    scrollX: 12,
    scrollY: 430,
    scrollTo: (options) => {
      restored.push(options)
      browser.scrollX = options.left
      browser.scrollY = options.top
    },
  }
  const dialog = {
    open: false,
    showModal() {
      this.open = true
      doc.activeElement = closeButton
    },
    close() {
      this.open = false
    },
    querySelector: () => closeButton,
    getBoundingClientRect: () => ({ left: 500, right: 1150, top: 0, bottom: 800 }),
  }
  globalThis.document = doc
  globalThis.window = browser
  try {
    await run({ html, body, before, restored, focused, closeFocused, dialog, doc, trigger })
  } finally {
    if (previousDocument === undefined) delete globalThis.document
    else globalThis.document = previousDocument
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
  }
}

test('drawer has one scrolling owner, fixed header, native Escape handling and unclipped detail', async () => {
  const css = await readFile(new URL('../src/assets/project-board.css', import.meta.url), 'utf8')
  const rules = (selector) =>
    [...css.matchAll(new RegExp(selector + '\\s*\\{([^}]+)\\}', 'g'))].at(-1)?.[1] || ''
  assert.match(rules('\\.projects-portal \\.drawer'), /overflow:\s*hidden/)
  assert.match(rules('\\.projects-portal \\.drawer-inner'), /min-height:\s*0/)
  assert.match(rules('\\.projects-portal \\.drawer-inner'), /overflow-y:\s*auto/)
  assert.match(rules('\\.projects-portal \\.drawer-head'), /flex-shrink:\s*0/)
  assert.match(rules('\\.projects-portal \\.drawer-inner > \\.pb-detail'), /overflow:\s*visible/)
  assert.match(source, /@cancel\.prevent="closeDetail"/)
  const html = await renderToString(createSSRApp(View))
  assert.match(
    html,
    /<dialog\b[\s\S]*?<header class="drawer-head"[\s\S]*?<\/header>\s*<div class="drawer-inner"/,
  )
})

test('all four chapter changes wait for rendering and locate content using only the drawer scroller', async () => {
  let state
  const Subject = {
    ...Detail,
    setup(props, context) {
      state = Detail.setup(props, context)
      return state
    },
  }
  await renderToString(createSSRApp(Subject, { project, stages }))
  const scrolls = []
  state.root.value = {
    querySelector: () => ({ getBoundingClientRect: () => ({ top: 300 }) }),
    closest: (selector) => {
      assert.equal(selector, '.drawer-inner')
      return {
        scrollTop: 120,
        getBoundingClientRect: () => ({ top: 40 }),
        scrollTo: (options) => scrolls.push(options),
      }
    },
  }
  for (const name of ['overview', 'progress', 'business', 'updates']) {
    const pending = state.selectSection(name)
    const count = scrolls.length
    await pending
    assert.equal(state.tab.value, name)
    assert.equal(scrolls.length, count + 1)
    assert.deepEqual(scrolls.at(-1), { top: 372, behavior: 'instant' })
  }
  const count = scrolls.length
  await Promise.all([state.selectSection('progress'), state.selectSection('updates')])
  assert.equal(state.tab.value, 'updates')
  assert.equal(scrolls.length, count + 1)
  await state.selectSection('not-a-section')
  assert.equal(scrolls.length, count + 1)
})

test('close, Escape cleanup and backdrop restore exact page styles, scroll and trigger focus once', async () => {
  await withDrawerDOM(async (context) => {
    const state = createState(async () => ({}))
    state.drawer.value = context.dialog
    for (const close of [
      () => state.closeDetail(),
      () => state.backdrop({ target: state.drawer.value, clientX: 10, clientY: 10 }),
    ]) {
      context.doc.activeElement = context.trigger
      await state.showDetail(123)
      assert.equal(context.body.style.getPropertyValue('position'), 'fixed')
      assert.equal(context.body.style.getPropertyValue('width'), '1000px')
      assert.equal(context.html.style.getPropertyValue('overflow-y'), 'hidden')
      close()
      state.closed() // queued native close event is idempotent
      assert.deepEqual(context.body.style.snapshot(), context.before.body)
      assert.deepEqual(context.html.style.snapshot(), context.before.html)
      assert.equal(state.detail.value, null)
    }
    assert.equal(context.restored.length, 2)
    assert.equal(context.focused.length, 2)
    assert.deepEqual(context.focused[0], { preventScroll: true })
    assert.deepEqual(context.closeFocused[0], { preventScroll: true })
    assert.deepEqual(context.restored[0], { left: 12, top: 430, behavior: 'instant' })
  })
})

test('closing pending requests, rapid reopening and unmount cannot leak scroll lock or stale detail', async () => {
  await withDrawerDOM(async (context) => {
    let resolveDetail, unmount
    const state = createState(
      async () => ({}),
      () =>
        new Promise((resolve) => {
          resolveDetail = resolve
        }),
      (callback) => {
        unmount = callback
      },
    )
    state.drawer.value = context.dialog
    const pending = state.showDetail(123)
    await nextTick()
    state.closeDetail()
    resolveDetail(project)
    await pending
    assert.equal(state.detail.value, null)
    assert.equal(state.detailLoading.value, false)
    const reopened = state.showDetail(124)
    await nextTick()
    state.closed() // old close event after reopening must not cancel this request
    resolveDetail({ ...project, id: 124 })
    await reopened
    assert.equal(state.detail.value.id, 124)
    const focusCount = context.focused.length
    unmount()
    assert.deepEqual(context.body.style.snapshot(), context.before.body)
    assert.deepEqual(context.html.style.snapshot(), context.before.html)
    assert.equal(context.focused.length, focusCount)
  })
})

test('view requests isolate perspectives and reject stale responses without hiding failures', async () => {
  const calls = []
  const state = createState(async (filters) => {
    calls.push(JSON.parse(JSON.stringify(filters)))
    return { projects: [], summary: {}, options: {}, stages }
  })
  state.overview.search = '仅总览搜索'
  await state.refresh()
  assert.equal(calls[0].search, '仅总览搜索')
  state.view.value = 'daily'
  state.updateDays.value = 7
  await state.refresh()
  assert.equal(calls[1].search, undefined)
  assert.equal(calls[1].update_days, 7)
  state.view.value = 'people'
  state.people.person = '虚构负责人'
  await state.refresh()
  assert.equal(calls[2].person, '虚构负责人')
  assert.equal(calls[2].search, undefined)
  assert.equal(calls[2].update_days, undefined)
  state.view.value = 'business'
  state.businesses.value = ['光伏', '储能']
  await state.refresh()
  assert.deepEqual(calls[3].business, ['光伏', '储能'])
  assert.equal(calls[3].person, undefined)
  const deferred = []
  const pending = createState(
    () => new Promise((resolve, reject) => deferred.push({ resolve, reject })),
  )
  const first = pending.refresh(),
    second = pending.refresh()
  deferred[1].resolve({ projects: [{ id: 2 }] })
  await second
  deferred[0].resolve({ projects: [{ id: 1 }] })
  await first
  assert.equal(pending.data.value.projects[0].id, 2)
  const failed = pending.refresh()
  deferred[2].reject(new Error('服务暂不可用'))
  await failed
  assert.equal(pending.error.value, '服务暂不可用')
  assert.equal(pending.loading.value, false)
})

test('non-editing employees can open /projects without any admin check', async () => {
  const { resolveAccess } = await server.ssrLoadModule('/src/utils/routeAccess.js')
  assert.equal(
    await resolveAccess(
      { name: 'projects', fullPath: '/projects', matched: [{ meta: {} }] },
      {
        employee: async () => ({ id: 1, mustChangePassword: false, canEditProjects: false }),
        admin: async () => {
          throw new Error('employee read must not ask for admin')
        },
      },
    ),
    true,
  )
})

test('display-only metric formatting retains unknown, zero, slash and raw data', () => {
  for (const [raw, value] of [
    ['5.89E-1', '0.589'],
    ['7.92E-2', '0.0792'],
    ['0.06699999999999999', '0.067'],
    ['0', '0'],
    ['/', '/'],
    ['尚不能确定', '尚不能确定'],
    [null, '未填写'],
  ])
    assert.equal(metricValue(raw), value)
  assert.equal(project.pvCapacity, '0.06699999999999999')
  assert.equal(currentPosition(project, stages), 7)
  assert.equal(currentPosition({ currentStage: '资料收集&方案设计' }, stages), 3)
  assert.equal(currentPosition({ currentStage: '未知阶段' }, stages), null)
})

test('B card and D detail share full business values and actual 11-node states', async () => {
  for (const Component of [Card, Detail]) {
    const html = await renderToString(createSSRApp(Component, { project, stages }))
    assert.ok(html.includes(project.energyScale))
    assert.ok(html.includes(project.situation))
    assert.match(html, /0\.067/)
    assert.match(html, /尚不能确定/)
    assert.doesNotMatch(html, /0\.06699999999999999|\d+%/)
    assert.match(html, /竣工投运/)
  }
  const detail = await renderToString(createSSRApp(Detail, { project, stages }))
  for (const title of ['项目概览', '实施进度', '项目内容', '实时情况', 'AG 原值'])
    assert.ok(detail.includes(title))
})

test('employee page renders empty state and four views without admin import controls', async () => {
  const html = await renderToString(createSSRApp(View))
  assert.match(html, /暂无项目台账/)
  for (const view of ['综合总览', '今日更新', '负责人', '项目业务']) assert.ok(html.includes(view))
  assert.doesNotMatch(html, /导出含数据|导入最新 Excel|file-input|imports\/confirm/)
  const source = await readFile(new URL('../src/views/ProjectsView.vue', import.meta.url), 'utf8')
  assert.doesNotMatch(source, /adminFetch|loadProjects\(|localStorage|project-dashboard\//)
  assert.match(source, /AbortController/)
})

test('employee service uses credentialed employee reads and OR query parameters', async () => {
  const { loadEmployeeProjects, loadEmployeeProjectDetail } = await server.ssrLoadModule(
    '/src/services/projects.js',
  )
  const previous = globalThis.fetch
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push([url, options])
    return new Response(JSON.stringify({ projects: [] }))
  }
  try {
    await loadEmployeeProjects({ view: 'business', business: ['光伏', '储能'] })
    await loadEmployeeProjectDetail(123)
    assert.match(calls[0][0], /\/api\/projects\?/)
    assert.equal(new URL(calls[0][0], 'http://test').searchParams.getAll('business').length, 2)
    assert.ok(calls[1][0].endsWith('/api/projects/123'))
    assert.ok(calls.every(([, options]) => options.credentials === 'include'))
  } finally {
    globalThis.fetch = previous
  }
})
