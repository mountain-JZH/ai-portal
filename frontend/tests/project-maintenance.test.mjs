import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { computed, createSSRApp, h, nextTick, reactive, ref } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'
import { createServer } from 'vite'
import {
  editableProject,
  projectChanges,
  projectFields,
  editorStages,
} from '../src/utils/projectEditor.js'
import { nodeDraftStage } from '../src/utils/projectNodes.js'
import { acquireModalPageLock } from '../src/utils/modalPageLock.js'

const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
})
after(() => server.close())
const editorSource = await readFile(
  new URL('../src/views/ProjectEditView.vue', import.meta.url),
  'utf8',
)
const historySource = await readFile(
  new URL('../src/components/ProjectHistoryDialog.vue', import.meta.url),
  'utf8',
)
function evaluate(source, dependencies, returns) {
  const setup = source
    .match(/<script setup>([\s\S]*?)<\/script>/)[1]
    .replace(/^import[\s\S]*?['"][^'"]+['"]\s*(?:\r?\n|$)/gm, '')
  return new Function(...Object.keys(dependencies), `${setup}; return {${returns}}`)(
    ...Object.values(dependencies),
  )
}
const original = {
  ...editableProject(),
  id: 42,
  version: 5,
  name: '虚构维护项目',
  storageCapacity: '尚不能确定单位',
  energyScale: '完整方案\n'.repeat(400),
  stages: [null, '自由状态原文', ...Array(9).fill(null)],
  currentStage: '合同签约',
}
function editor(options = {}) {
  const route = reactive({ params: { id: options.new ? undefined : '42' } })
  const calls = [],
    guards = [],
    employee = ref({ canEditProjects: !options.denied })
  const state = evaluate(
    editorSource,
    {
      computed,
      reactive,
      ref,
      watch: () => {},
      onMounted: () => {},
      onBeforeUnmount: () => {},
      onBeforeRouteLeave: (fn) => guards.push(fn),
      onBeforeRouteUpdate: () => {},
      useRoute: () => route,
      useRouter: () => ({
        replace: async () => {
          route.params.id = '42'
        },
      }),
      currentEmployee: employee,
      editableProject,
      projectChanges,
      projectFields,
      editorStages,
      nodeDraftStage,
      loadEmployeeProjectDetail:
        options.read || (async () => ({ ...original, ...options.updated })),
      loadProjectHistory: async () => ({ items: [] }),
      saveEmployeeProject: async (...args) => {
        calls.push(args)
        if (options.failure)
          throw Object.assign(new Error('虚构保存失败'), { status: options.failure })
        return { ...original, ...args[2], version: 6 }
      },
    },
    'form,project,original,load,save,dirty,error,success,conflict,confirmLeave,beforeUnload,mode,title,isNew,updateNodes,businessGroups,openBusinesses,switchMode,initializeBusinessGroups',
  )
  return { ...state, calls, route, guards, employee }
}

test('editor retains all raw fields, unknown units, long text and independent 11-node states', async () => {
  const state = editor()
  await state.load()
  assert.deepEqual({ ...state.form }, editableProject(original))
  state.form.situation = '仅修改 AD'
  assert.deepEqual(projectChanges(state.form, state.original.value), { situation: '仅修改 AD' })
  assert.notEqual(state.form.stages, original.stages)
  assert.equal(state.form.stages[0], null)
  assert.equal(state.form.currentStage, '合同签约')
  assert.equal(Object.keys(state.form).length, 21)
})

test('save sends only changed fields and successful response is reread; no-op does not send writes', async () => {
  const oldWindow = globalThis.window
  globalThis.window = { confirm: () => true }
  try {
    const state = editor({ updated: { situation: '服务端新内容' } })
    await state.load()
    await state.save()
    assert.equal(state.calls.length, 0)
    state.form.situation = '服务端新内容'
    state.form.nextStep = '新计划'
    await state.save()
    assert.deepEqual(state.calls[0], [42, 5, { nextStep: '新计划' }])
    assert.match(state.success.value, /保存成功/)
    assert.equal(state.dirty.value, false)
  } finally {
    globalThis.window = oldWindow
  }
})

test('409 and failed save retain drafts without claiming success, cancellation and unload guard work', async () => {
  const oldWindow = globalThis.window
  try {
    for (const failure of [409, 500]) {
      globalThis.window = { confirm: () => true }
      const state = editor({ failure })
      await state.load()
      state.form.coordination = '必须保留的草稿'
      await state.save()
      assert.equal(state.form.coordination, '必须保留的草稿')
      assert.equal(state.success.value, '')
      assert.equal(state.conflict.value, failure === 409)
      globalThis.window.confirm = () => false
      assert.equal(state.confirmLeave(), false)
      let prevented = false
      state.beforeUnload({
        preventDefault: () => {
          prevented = true
        },
      })
      assert.equal(prevented, true)
      await state.save()
      assert.equal(state.calls.length, 1)
    }
  } finally {
    globalThis.window = oldWindow
  }
})

test('unauthorized editor and failed detail load cannot fall back to project creation', async () => {
  const state = editor({ denied: true })
  await state.load()
  await state.save()
  assert.equal(state.calls.length, 0)
  assert.equal(state.project.value, null)
  const failed = editor({
    read: async () => {
      throw new Error('虚构 404')
    },
  })
  await failed.load()
  failed.form.name = '不得意外创建'
  await failed.save()
  assert.equal(failed.calls.length, 0)
  assert.match(failed.error.value, /404/)
})

test('existing projects default to daily progress; switching modes preserves every draft and shared version', async () => {
  const state = editor()
  await state.load()
  assert.equal(state.mode.value, 'progress')
  assert.equal(state.title.value, '更新项目进展')
  state.form.situation = '日常模式未保存的长文本\n'.repeat(80)
  state.switchMode('archive')
  assert.equal(state.title.value, '维护项目档案')
  state.form.owner = '虚构档案负责人'
  state.switchMode('progress')
  assert.equal(state.form.owner, '虚构档案负责人')
  assert.equal(state.form.situation, '日常模式未保存的长文本\n'.repeat(80))
  assert.deepEqual(Object.keys(projectChanges(state.form, state.original.value)).sort(), [
    'owner',
    'situation',
  ])
  assert.equal(state.project.value.version, 5)
})

test('node edits synchronize earliest active only in draft, undo restores original AC and special values', async () => {
  const state = editor()
  await state.load()
  assert.equal(state.dirty.value, false)
  const nodes = [...state.form.stages]
  nodes[4] = '进行中'
  nodes[8] = '进行中'
  nodes[0] = '已完成'
  state.updateNodes(nodes)
  assert.equal(state.form.currentStage, '可研编制')
  assert.equal(state.form.stages[1], '自由状态原文')
  assert.equal(state.calls.length, 0)
  nodes[2] = '进行中'
  state.updateNodes(nodes)
  assert.equal(state.form.currentStage, '资料收集与方案设计')
  state.updateNodes([...state.original.value.stages])
  assert.equal(state.form.currentStage, '合同签约')
  assert.equal(state.dirty.value, false)
})

test('no active nodes preserve historical AC; unrelated edits never synchronize imported AC', async () => {
  const state = editor({
    updated: { currentStage: '原台账阶段', stages: ['进行中', ...Array(10).fill(null)] },
  })
  await state.load()
  assert.equal(state.form.currentStage, '原台账阶段')
  state.form.situation = '只修改文字'
  assert.deepEqual(projectChanges(state.form, state.original.value), { situation: '只修改文字' })
  state.updateNodes(['已完成', '未开始', '暂缓', '不适用', '', ...Array(6).fill(null)])
  assert.equal(state.form.currentStage, '原台账阶段')
  assert.equal(state.form.stages[4], '')
  assert.equal(state.calls.length, 0)
})

test('business disclosure defaults follow actual raw values and collapsing never clears values', async () => {
  const state = editor()
  await state.load()
  assert.deepEqual(
    { ...state.openBusinesses },
    { pv: false, storage: true, charging: false, energy: true },
  )
  state.switchMode('archive')
  state.openBusinesses.pv = true
  state.form.pvCapacity = '尚不能确定'
  state.form.pvArea = '0'
  state.openBusinesses.pv = false
  state.switchMode('progress')
  state.switchMode('archive')
  assert.equal(state.openBusinesses.pv, false)
  assert.equal(state.form.pvCapacity, '尚不能确定')
  assert.equal(state.form.energyScale, original.energyScale)
  state.initializeBusinessGroups()
  assert.equal(state.openBusinesses.pv, true)
  state.form.stages[3] = '不适用：保留原文'
  state.form.stages[10] = '未开始'
  assert.equal(state.form.stages[3], '不适用：保留原文')
  assert.equal(state.form.stages[10], '未开始')
})

test('new project defaults to complete archive and sends initial narrative, business and nodes together', async () => {
  const oldWindow = globalThis.window
  globalThis.window = { confirm: () => true }
  try {
    const state = editor({ new: true })
    await state.load()
    assert.equal(state.mode.value, 'archive')
    assert.equal(state.title.value, '新增项目')
    state.switchMode('progress')
    assert.equal(state.mode.value, 'archive')
    state.form.name = '完全虚构的新建测试项目'
    state.form.storageCapacity = '尚不能确定，单位待确认'
    const nodes = [...state.form.stages]
    nodes[6] = '进行中'
    state.updateNodes(nodes)
    state.form.stages[1] = '暂缓'
    state.form.situation = '虚构初始实施情况'
    state.form.nextStep = '虚构下一步'
    await state.save()
    assert.equal(state.calls.length, 1)
    const [id, version, payload] = state.calls[0]
    assert.equal(id, undefined)
    assert.equal(version, undefined)
    assert.equal(payload.name, '完全虚构的新建测试项目')
    assert.equal(payload.situation, '虚构初始实施情况')
    assert.equal(payload.stages[6], '进行中')
    assert.equal(payload.stages[0], null)
    assert.equal(payload.storageCapacity, '尚不能确定，单位待确认')
  } finally {
    globalThis.window = oldWindow
  }
})

test('compiled daily template omits archive inputs, new route includes all groups and initial narratives', async () => {
  const { currentEmployee } = await server.ssrLoadModule('/src/utils/authState.js')
  const { default: Editor } = await server.ssrLoadModule('/src/views/ProjectEditView.vue')
  const previous = currentEmployee.value
  currentEmployee.value = { canEditProjects: true }
  try {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/projects', component: { render: () => null } },
        { path: '/projects/new', component: Editor },
        { path: '/projects/:id/edit', component: Editor },
      ],
    })
    await router.push('/projects/42/edit')
    await router.isReady()
    const daily = await renderToString(createSSRApp({ render: () => h(RouterView) }).use(router))
    assert.match(daily, /更新项目进展/)
    assert.doesNotMatch(daily, /id="editor-basic-title"|id="editor-business-title"/)
    assert.equal((daily.match(/<textarea/g) || []).length, 3)
    assert.equal((daily.match(/data-node-id=/g) || []).length, 11)
    assert.match(daily, /高级状态编辑/)
    assert.equal((daily.match(/<select/g) || []).length, 0)
    for (const name of editorStages) assert.ok(daily.includes(name.replaceAll('&', '&amp;')), name)
    for (const status of ['已完成', '进行中', '未开始', '暂缓', '不适用'])
      assert.ok(daily.includes(status))
    await router.push('/projects/new')
    const create = await renderToString(createSSRApp({ render: () => h(RouterView) }).use(router))
    assert.match(create, /id="editor-basic-title"/)
    const basic = create.match(
      /<section[^>]*aria-labelledby="editor-basic-title"[\s\S]*?<\/section>/,
    )[0]
    assert.equal((basic.match(/class="editor-basic-label"/g) || []).length, 5)
    assert.match(
      basic,
      /<label[^>]*>\s*<span class="editor-basic-label"[^>]*>\s*项目名称\s*<span[^>]*>（必填）<\/span>\s*<\/span>\s*<input[^>]*required/,
    )
    assert.match(basic, /<label[^>]*>\s*<span class="editor-basic-label"[^>]*>\s*资源名称 \/ 来源/)
    assert.match(
      editorSource,
      /\.editor-basic-label\s*\{[^}]*height: 1\.7em;[^}]*white-space: nowrap;/,
    )
    assert.match(create, /id="editor-attributes-title"/)
    assert.match(create, /初始实时情况（可选）/)
    assert.equal((create.match(/class="editor-business"/g) || []).length, 4)
    assert.match(create, /data-node-id="stage_11"/)
    assert.doesNotMatch(create, /class="editor-all-nodes" open/)
  } finally {
    currentEmployee.value = previous
  }
})

test('editor route renders explicit permission denial; only authorized D detail has edit link', async () => {
  const { currentEmployee } = await server.ssrLoadModule('/src/utils/authState.js')
  const { default: Editor } = await server.ssrLoadModule('/src/views/ProjectEditView.vue')
  const { default: Detail } = await server.ssrLoadModule(
    '/src/components/ProjectReadOnlyDetail.vue',
  )
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:pathMatch(.*)*', component: Editor }],
  })
  await router.push('/projects/42/edit')
  await router.isReady()
  const previous = currentEmployee.value
  try {
    currentEmployee.value = { canEditProjects: false }
    const denied = await renderToString(createSSRApp({ render: () => h(RouterView) }).use(router))
    assert.match(denied, /没有项目维护权限/)
    assert.doesNotMatch(denied, /<form/)
    const props = { project: original, stages: editorStages, section: 'overview' }
    const read = await renderToString(createSSRApp(Detail, props).use(router))
    assert.doesNotMatch(read, /编辑项目<\/a>/)
    currentEmployee.value = { canEditProjects: true }
    const allowed = await renderToString(createSSRApp({ render: () => h(RouterView) }).use(router))
    assert.match(allowed, /<form/)
    const edit = await renderToString(createSSRApp(Detail, props).use(router))
    assert.match(edit, /href="\/projects\/42\/edit"/)
  } finally {
    currentEmployee.value = previous
  }
})

test('history open, paging and close preserve focus and release only its lock', async () => {
  const oldDocument = globalThis.document
  let restored = 0,
    releases = 0,
    unmount
  const trigger = {
    isConnected: true,
    focus: (options) => {
      assert.equal(options.preventScroll, true)
      restored++
    },
  }
  globalThis.document = { activeElement: trigger }
  const queries = []
  try {
    const state = evaluate(
      historySource,
      {
        ref,
        nextTick,
        projectFields,
        editorStages,
        onBeforeUnmount: (fn) => {
          unmount = fn
        },
        defineExpose: () => {},
        acquireModalPageLock: () => () => {
          releases++
        },
        loadProjectHistory: async (id, field, offset) => {
          queries.push([id, field, offset])
          return { total: 2, items: [{ id: offset + 1, new_value: '完整\n内容' }] }
        },
      },
      'dialog,project,field,items,total,error,open,load,close,closed,backdrop',
    )
    state.dialog.value = {
      open: false,
      showModal() {
        this.open = true
      },
      close() {
        this.open = false
      },
      querySelector: () => ({ focus: () => {} }),
      getBoundingClientRect: () => ({ left: 10, right: 100, top: 10, bottom: 100 }),
    }
    await state.open(original, 'situation')
    await state.load(true)
    assert.deepEqual(queries, [
      [42, 'situation', 0],
      [42, 'situation', 1],
    ])
    assert.equal(state.items.value.length, 2)
    state.backdrop({ target: state.dialog.value, clientX: 0, clientY: 0 })
    state.closed()
    assert.equal(releases, 1)
    assert.equal(restored, 1)
    await state.open(original, 'coordination')
    unmount()
    assert.equal(releases, 2)
    assert.match(historySource, /@cancel\.prevent="close"/)
    assert.match(historySource, /white-space: pre-wrap/)
    assert.match(historySource, /暂无后续修改记录/)
    assert.doesNotMatch(historySource, /v-html/)
  } finally {
    globalThis.document = oldDocument
  }
})

test('nested drawer and history owners unlock background only after the last close', () => {
  const oldDocument = globalThis.document,
    oldWindow = globalThis.window
  const style = () => {
    const map = new Map()
    return {
      getPropertyValue: (key) => map.get(key) || '',
      getPropertyPriority: () => '',
      setProperty: (key, value) => map.set(key, value),
      removeProperty: (key) => map.delete(key),
    }
  }
  const body = {
    style: style(),
    getBoundingClientRect: () => ({ top: -200, left: 0, width: 1200 }),
  }
  let restored
  globalThis.document = { body, documentElement: { style: style() } }
  globalThis.window = {
    scrollX: 0,
    scrollY: 200,
    scrollTo: (value) => {
      restored = value
    },
  }
  try {
    const drawer = acquireModalPageLock(),
      history = acquireModalPageLock()
    drawer()
    assert.equal(body.style.getPropertyValue('position'), 'fixed')
    history()
    history()
    assert.equal(body.style.getPropertyValue('position'), '')
    assert.equal(restored.top, 200)
  } finally {
    globalThis.document = oldDocument
    globalThis.window = oldWindow
  }
})
