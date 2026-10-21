import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createServer } from 'vite'
import { readFile } from 'node:fs/promises'
import { beijingDay, projectUpdateLabel } from '../src/utils/projectUpdates.js'
import { editorStages } from '../src/utils/projectEditor.js'

const server = await createServer({
  server: { middlewareMode: true, hmr: false },
  appType: 'custom',
})
after(() => server.close())
const { default: Card } = await server.ssrLoadModule('/src/components/ProjectBoardCard.vue')
const { default: View } = await server.ssrLoadModule('/src/views/ProjectsView.vue')
const now = new Date('2026-10-21T03:00:00Z')
const project = {
  id: 42,
  name: '虚构字段日期测试项目',
  stages: [null, '进行中', null, '进行中', ...Array(7).fill(null)],
  completedCount: 0,
  currentStage: '实地勘察',
  businessTypes: [],
  situation: '虚构 AD',
  nextStep: '虚构 AE',
  coordination: '虚构 AF',
  progressUpdate: '有',
  updated: false,
}
const htmlFor = (data) =>
  renderToString(createSSRApp(Card, { project: data, stages: editorStages, now }))

test('Shanghai natural day, next-day persistence and cross-year date format', () => {
  assert.equal(projectUpdateLabel('2026-10-20T16:00:00Z', now), '今日更新')
  assert.equal(projectUpdateLabel('2026-10-20T15:59:59Z', now), '10月20日更新')
  assert.equal(
    projectUpdateLabel('2026-10-21T01:00:00Z', new Date('2026-10-22T01:00:00Z')),
    '10月21日更新',
  )
  assert.equal(projectUpdateLabel('2025-12-31T15:59:59Z', now), '2025年12月31日更新')
  assert.equal(
    projectUpdateLabel('2026-12-31T16:00:00Z', new Date('2027-01-01T01:00:00Z')),
    '今日更新',
  )
  assert.equal(
    projectUpdateLabel('2026-12-31T15:59:59Z', new Date('2027-01-01T01:00:00Z')),
    '2026年12月31日更新',
  )
  assert.equal(projectUpdateLabel(null, now), '')
  assert.equal(projectUpdateLabel('invalid', now), '')
  assert.equal(beijingDay(now).key, '2026-10-21')
})

test('one persistent project-level badge follows the ID; internal dates and dots are absent', async () => {
  for (const [at, label, today] of [
    ['2026-10-21T01:00:00Z', '今日更新', true],
    ['2026-10-20T01:00:00Z', '10月20日更新', false],
    ['2025-10-21T01:00:00Z', '2025年10月21日更新', false],
  ]) {
    const html = await htmlFor({
      ...project,
      latestBusinessUpdateAt: at,
      fieldUpdates: { situation: at, nextStep: at, coordination: at },
      nodesUpdatedAt: at,
    })
    assert.equal((html.match(/class="project-update-badge\b/g) || []).length, 1)
    assert.match(html, /class="card-topline"[^>]*><span[^>]*>项目 \/ 042<\/span>\s*<time/)
    assert.ok(html.includes(label))
    assert.equal(/class="project-update-badge is-today"/.test(html), today)
    const middle = html.match(
      /<section class="cardcol card-mid"[\s\S]*?<section class="cardcol card-right"/,
    )[0]
    assert.doesNotMatch(middle, /project-update-badge|<time|今日更新|月\d+日更新/)
    assert.equal((middle.match(/class="project-history-entry"/g) || []).length, 3)
    assert.equal((middle.match(/class="timeline-unit"/g) || []).length, 11)
    assert.equal(
      (middle.match(/class="(?=[^"]*\btimeline-rect\b)(?=[^"]*\bactive\b)[^"]*"/g) || []).length,
      2,
    )
    for (const body of [project.situation, project.nextStep, project.coordination])
      assert.ok(middle.includes(body))
  }
})

test('AG, creation metadata or field dates alone cannot manufacture project update badges', async () => {
  const html = await htmlFor({
    ...project,
    updated: true,
    updatedAt: now.toISOString(),
    createdAt: now.toISOString(),
    fieldUpdates: { situation: now.toISOString() },
    nodesUpdatedAt: now.toISOString(),
  })
  assert.doesNotMatch(html, /project-update-badge|暂无更新|本次标记更新/)
  const source = await readFile(
    new URL('../src/components/ProjectBoardCard.vue', import.meta.url),
    'utf8',
  )
  assert.equal((source.match(/<ProjectUpdateBadge/g) || []).length, 1)
  assert.match(source, /:at="project.latestBusinessUpdateAt"/)
  assert.doesNotMatch(source, /padding-inline-end: 44px/)
  assert.match(source, /\.project-card \.card-topline\s*\{[^}]*height: 1\.5em;/)
})

test('daily view has one scoped date control, no overview filter and fixed recency sort', async () => {
  const Daily = {
    ...View,
    setup(props, context) {
      const state = View.setup(props, context)
      state.view.value = 'daily'
      return state
    },
  }
  const html = await renderToString(createSSRApp(Daily))
  for (const label of ['今日', '近 7 天', '近 30 天', '北京时间']) assert.ok(html.includes(label))
  assert.match(html, /aria-label="更新日期范围"/)
  assert.match(html, /class="update-range-select"/)
  assert.doesNotMatch(html, /class="filterbar"|id="sortSelect"|本次标记更新/)
  const source = await readFile(new URL('../src/views/ProjectsView.vue', import.meta.url), 'utf8')
  assert.match(source, /clearInterval\(clockTimer\)/)
  assert.match(source, /previous !== beijingDay\(updateClock.value\)\?\.key/)
})

test('range selection cannot change a project badge date; daily and history badges share geometry', async () => {
  for (const days of [1, 7, 30]) {
    const Daily = {
      ...View,
      setup(props, context) {
        const state = View.setup(props, context)
        state.view.value = 'daily'
        state.updateDays.value = days
        state.updateClock.value = now
        state.data.value = {
          projects: [{ ...project, latestBusinessUpdateAt: '2026-10-20T01:00:00Z' }],
          summary: {},
          stages: editorStages,
        }
        return state
      },
    }
    const html = await renderToString(createSSRApp(Daily))
    assert.match(html, /10月20日更新/)
    assert.equal((html.match(/class="project-update-badge\b/g) || []).length, 1)
  }
  const css = await readFile(new URL('../src/assets/project-board.css', import.meta.url), 'utf8')
  assert.match(
    css,
    /\.filter-top select,\s*\.projects-portal \.filter-more select,\s*\.projects-portal \.update-range-select\s*\{[^}]*height: 40px/,
  )
  const badge = await readFile(
    new URL('../src/components/ProjectUpdateBadge.vue', import.meta.url),
    'utf8',
  )
  for (const rule of [
    'height: 24px',
    'font-size: 12px',
    'font-weight: 600',
    'border-radius: 6px',
    'background: #fff3d8',
  ])
    assert.ok(badge.includes(rule))
  assert.match(badge, /\.project-update-badge\.is-today\s*\{[^}]*#f7b334/)
  assert.doesNotMatch(badge, /aria-hidden|box-shadow|animation:/)
})
