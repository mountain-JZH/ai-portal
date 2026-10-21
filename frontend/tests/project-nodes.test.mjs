import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { computed, createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createServer } from 'vite'
import { readFile } from 'node:fs/promises'
import { firstActiveNode, nextNodeStatus, nodeDraftStage } from '../src/utils/projectNodes.js'
import { currentPosition, currentStageName, shortStages } from '../src/utils/projectBoard.js'
import { editorStages } from '../src/utils/projectEditor.js'

const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
})
after(() => server.close())
const { default: Editor } = await server.ssrLoadModule('/src/components/ProjectNodeEditor.vue')

test('exact three-state cycle, blanks and special text remain semantically distinct', () => {
  for (const value of [null, '', '未开始', '暂缓', '不适用', '进行中：旧文本', ' 自定义 ']) {
    assert.equal(nextNodeStatus(value), '进行中')
    assert.equal(firstActiveNode([value]), -1)
  }
  assert.equal(nextNodeStatus('进行中'), '已完成')
  assert.equal(nextNodeStatus('已完成'), null)
})

test('earliest active wins independently; no-active and undo retain original AC without mutation', () => {
  const baseline = [null, '未开始', '暂缓', '', ...Array(7).fill(null)]
  const nodes = [...baseline]
  nodes[8] = '进行中'
  assert.equal(nodeDraftStage(nodes, baseline, '历史AC', editorStages), '招标')
  nodes[2] = '进行中'
  nodes[4] = '已完成'
  assert.equal(nodeDraftStage(nodes, baseline, '历史AC', editorStages), '资料收集与方案设计')
  const project = { currentStage: '历史AC', stages: nodes }
  assert.equal(currentPosition(project, editorStages), 3)
  assert.equal(currentStageName(project, editorStages), editorStages[2])
  assert.equal(project.currentStage, '历史AC')
  nodes[2] = '已完成'
  nodes[8] = '未开始'
  assert.equal(nodeDraftStage(nodes, baseline, '历史AC', editorStages), '历史AC')
  assert.equal(nodeDraftStage([...baseline], baseline, '历史AC', editorStages), '历史AC')
  assert.deepEqual(baseline.slice(0, 4), [null, '未开始', '暂缓', ''])
})

test('real editor click and undo handlers emit draft copies only and obey disabled', async () => {
  const source = await readFile(
    new URL('../src/components/ProjectNodeEditor.vue', import.meta.url),
    'utf8',
  )
  const setup = source
    .match(/<script setup>([\s\S]*?)<\/script>/)[1]
    .replace(/^import[^\n]+\n/gm, '')
  const props = {
    modelValue: [null, '暂缓', ...Array(9).fill(null)],
    baseline: [null, '暂缓', ...Array(9).fill(null)],
    disabled: false,
  }
  const events = []
  const state = new Function(
    'computed',
    'defineProps',
    'defineEmits',
    'editorStages',
    'shortStages',
    'firstActiveNode',
    'nextNodeStatus',
    `${setup};return {cycle,setNode,undo}`,
  )(
    computed,
    () => props,
    () => (name, nodes) => {
      events.push([name, nodes])
      props.modelValue = nodes
    },
    editorStages,
    shortStages,
    firstActiveNode,
    nextNodeStatus,
  )
  state.cycle(0)
  state.cycle(4)
  assert.equal(firstActiveNode(props.modelValue), 0)
  state.cycle(0)
  assert.equal(props.modelValue[0], '已完成')
  assert.equal(props.modelValue[4], '进行中')
  state.cycle(0)
  assert.equal(props.modelValue[0], null)
  assert.equal(props.modelValue[1], '暂缓')
  state.undo()
  assert.deepEqual(props.modelValue, props.baseline)
  assert.notEqual(props.modelValue, props.baseline)
  const count = events.length
  props.disabled = true
  state.cycle(0)
  state.setNode(1, '')
  state.undo()
  assert.equal(events.length, count)
  assert.ok(events.every(([name]) => name === 'update:modelValue'))
})

test('SSR editor has 11 accessible buttons, raw advanced text, no selects and independent colors', async () => {
  const nodes = [
    '已完成',
    '进行中',
    null,
    '进行中',
    '未开始',
    '暂缓',
    '不适用',
    '',
    '原始特殊状态',
    null,
    null,
  ]
  const html = await renderToString(
    createSSRApp(Editor, { modelValue: nodes, baseline: [...nodes], currentStage: '历史AC' }),
  )
  assert.equal((html.match(/data-node-id="stage_/g) || []).length, 11)
  assert.equal((html.match(/class="active"/g) || []).length, 2)
  assert.equal((html.match(/class="done"/g) || []).length, 1)
  assert.match(html, /实地勘察/)
  assert.match(html, /value="原始特殊状态"/)
  assert.match(html, /高级状态编辑/)
  assert.doesNotMatch(html, /<select|<details[^>]* open/)
  assert.match(html, /aria-label="01 客户对接，已完成/)
  const blank = await renderToString(
    createSSRApp(Editor, {
      modelValue: Array(11).fill(null),
      baseline: Array(11).fill(null),
      currentStage: '保留历史阶段',
    }),
  )
  assert.match(blank, /当前没有进行中的节点/)
  assert.match(blank, /保留历史阶段/)
})
