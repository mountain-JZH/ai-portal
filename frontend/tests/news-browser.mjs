import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import process from 'node:process'
import { createServer as createNetServer } from 'node:net'
import { mkdtemp, readFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { createServer } from 'vite'
const { chromium } = await import(pathToFileURL(path.join(tmpdir(), 'ai-portal-browser-tools/node_modules/playwright/index.mjs')).href)
const output = await mkdtemp(path.join(tmpdir(), 'news-browser-'))
const base = 'http://127.0.0.1:15173'
// Fail closed if a developer's service already owns either test port.
for (const port of [15173, 18080]) {
  await new Promise((resolve, reject) => {
    const probe = createNetServer()
    probe.once('error', reject)
    probe.listen(port, '127.0.0.1', () => probe.close(resolve))
  })
}
const testAdmin = `browser-${randomBytes(6).toString('hex')}`
const testPassword = randomBytes(32).toString('hex')
const backend = spawn('../backend/.venv/Scripts/python.exe', ['-B', '../backend/tests/news_browser_server.py'], {
  stdio: ['ignore', 'pipe', 'pipe'],
  env: {
    ...process.env,
    NEWS_BROWSER_ADMIN_USERNAME: testAdmin,
    NEWS_BROWSER_ADMIN_PASSWORD: testPassword,
    NEWS_BROWSER_SESSION_SECRET: randomBytes(32).toString('hex'),
  },
})
let backendErrors = ''
backend.stderr.on('data', data => { backendErrors += data.toString() })
process.env.VITE_API_BASE_URL = '/api'
let server, browser
const checks = []
try {
  for (let i = 0; ; i++) {
    try { if ((await fetch('http://127.0.0.1:18080/api/health')).ok) break } catch { /* startup */ }
    if (i > 100 || backend.exitCode !== null) throw new Error('Isolated API startup failed: ' + backendErrors)
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  server = await createServer({ server: { host: '127.0.0.1', port: 15173, strictPort: true, hmr: false,
    proxy: { '/api': 'http://127.0.0.1:18080', '/uploads': 'http://127.0.0.1:18080' } } })
  await server.listen()
  browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true })
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  await page.goto(base + '/news/1')
  await page.getByRole('heading', { name: '普通新闻测试', exact: true }).waitFor()
  assert.equal(await page.locator('.content strong').count(), 0)
  assert.match(await page.locator('.content').innerText(), /\*\*保留原文\*\*/)
  checks.push('ordinary news remains plain text')
  await page.goto(base + '/news/2')
  await page.getByRole('heading', { name: '今日速览', exact: true }).waitFor()
  assert.equal(await page.locator('h1').count(), 1)
  for (const name of ['今日重点', '江苏及周边动态', '行业快讯', '持续关注']) await page.getByRole('heading', { name, exact: true }).waitFor()
  assert.equal(await page.locator('.content script,.content iframe,.content img').count(), 0)
  assert.equal(await page.evaluate(() => window.__newsXss), undefined)
  assert.equal(await page.locator('.content a[href^="javascript:"]').count(), 0)
  const link = page.getByRole('link', { name: '测试来源', exact: true })
  assert.equal(await link.getAttribute('rel'), 'noopener noreferrer')
  await context.route('https://example.com/energy', route => route.fulfill({ contentType: 'text/html', body: '<h1>Test source</h1>' }))
  const popupPromise = page.waitForEvent('popup')
  await link.click()
  const popup = await popupPromise
  await popup.waitForLoadState()
  assert.equal(popup.url(), 'https://example.com/energy')
  await popup.close()
  await page.screenshot({ path: path.join(output, 'brief-desktop.png'), fullPage: true })
  for (const width of [375, 320]) {
    await page.setViewportSize({ width, height: 812 })
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'brief horizontal overflow at ' + width)
  }
  await page.screenshot({ path: path.join(output, 'brief-mobile.png'), fullPage: true })
  checks.push('five sections, safe links, XSS blocking, 1440/375/320 layouts')
  assert.equal((await context.request.get(base + '/api/news/3')).status(), 404)
  assert.equal((await context.request.get(base + '/api/admin/news/3')).status(), 401)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(base + '/admin/news/3/edit')
  await page.getByRole('heading', { name: '管理后台登录' }).waitFor()
  await page.getByLabel('用户名').fill(testAdmin)
  await page.getByLabel('密码', { exact: true }).fill(testPassword)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByPlaceholder('请输入新闻标题').waitFor()
  assert.equal(await page.getByRole('checkbox').isChecked(), false)
  await page.getByPlaceholder('请输入新闻标题').fill('隔离草稿修改')
  await page.getByRole('button', { name: '保存修改', exact: true }).click()
  await page.getByText(/新闻修改成功|草稿保存成功/).waitFor()
  const draft = await (await context.request.get(base + '/api/admin/news/3')).json()
  assert.equal(draft.title, '隔离草稿修改')
  assert.equal(draft.is_published, 0)
  assert.equal((await context.request.get(base + '/api/news/3')).status(), 404)
  await page.setViewportSize({ width: 375, height: 812 })
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'editor horizontal overflow')
  await page.screenshot({ path: path.join(output, 'editor-mobile.png'), fullPage: true })
  checks.push('real admin login/draft edit preserves privacy on desktop/mobile')
  if (!process.argv.includes('--phase2')) {
    const { checkPhase3 } = await import('./news-browser-flow.mjs')
    await checkPhase3({ page, context, base, output, checks, sample: await readFile('../backend/tests/fixtures/news-brief.md', 'utf8') })
  }
  assert.deepEqual(errors, [])
  console.log(JSON.stringify({ checks, screenshots: output, pageErrors: errors }, null, 2))
} finally {
  backend.kill()
  // Vite plugins may retain websocket handles after successful browser checks.
  await Promise.race([
    Promise.all([browser?.close(), server?.close()]),
    new Promise(resolve => setTimeout(resolve, 5000)),
  ])
}
process.exit(0)
