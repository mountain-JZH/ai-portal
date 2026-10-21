import assert from 'node:assert/strict'
import { after, test } from 'node:test'
import { createServer } from 'vite'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' })
after(() => server.close())
const auth = await server.ssrLoadModule('/src/utils/employeeAuth.js')
const state = await server.ssrLoadModule('/src/utils/authState.js')
const { personalStorage } = await server.ssrLoadModule('/src/utils/personalStorage.js')
const { resolveAccess } = await server.ssrLoadModule('/src/utils/routeAccess.js')
const route = (name, fullPath, admin = false, query = {}) => ({ name, fullPath, query, matched: [{ meta: { requiresAdmin: admin } }] })

test('all routes require login; admin access follows the single server-provided identity', async () => {
  for (const path of ['/', '/news', '/news/1', '/exchange', '/tools', '/assistant', '/projects', '/admin']) {
    const result = await resolveAccess(route('test', path, path === '/admin'), { employee: async () => null })
    assert.equal(result.name, 'login'); assert.equal(result.query.redirect, path)
  }
  const employee = async () => ({ id: 1, mustChangePassword: false, canEditProjects: true, isAdmin: false })
  const checks = { employee, admin: async () => { throw new Error('No second authentication should run') } }
  assert.equal(await resolveAccess(route('home', '/'), checks), true)
  assert.equal((await resolveAccess(route('admin', '/admin', true), checks)).name, 'home')
  assert.equal(await resolveAccess(route('admin', '/admin', true), { employee: async () => ({ id: 1, isAdmin: true }) }), true)
})

test('legacy first-login flag no longer blocks browsing; return targets remain internal', async () => {
  const first = { employee: async () => ({ id: 1, mustChangePassword: true }) }
  assert.equal(await resolveAccess(route('home', '/'), first), true)
  assert.equal(await resolveAccess(route('change-password', '/change-password'), first), true)
  for (const path of ['https://attacker.invalid', '//attacker.invalid', '/\\attacker.invalid', '/login', '/admin/login']) {
    assert.equal(auth.safeReturnPath(path), '/')
  }
  assert.equal(auth.safeReturnPath('/news/25?view=full'), '/news/25?view=full')
  assert.equal(await resolveAccess(route('login', '/login', false, { redirect: '/news/25' }), { employee: async () => ({ id: 1 }) }), '/news/25')
})

test('personal storage cannot mix employee identities or adopt anonymous legacy data', () => {
  const original = globalThis.localStorage
  const values = new Map([['todos', 'legacy-data']])
  globalThis.localStorage = { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) }
  try {
    state.currentEmployee.value = null; assert.equal(personalStorage.getItem('todos'), null)
    state.currentEmployee.value = { id: 1 }; assert.equal(personalStorage.getItem('todos'), null)
    personalStorage.setItem('todos', 'employee-one')
    state.currentEmployee.value = { id: 2 }; assert.equal(personalStorage.getItem('todos'), null)
    personalStorage.setItem('todos', 'employee-two')
    state.currentEmployee.value = { id: 1 }; assert.equal(personalStorage.getItem('todos'), 'employee-one')
    state.clearIdentity(); assert.equal(personalStorage.getItem('todos'), null)
    assert.equal(values.get('todos'), 'legacy-data')
  } finally { globalThis.localStorage = original; state.clearIdentity() }
})

test('requests include cookie and CSRF without assigning multipart Content-Type, expiry clears identities', async () => {
  const original = globalThis.fetch
  const calls = []
  state.csrfToken.value = 'unit-test-csrf'
  state.currentEmployee.value = { id: 1 }; state.currentAdmin.value = { id: 2 }
  globalThis.fetch = async (url, init) => { calls.push(init); return new Response('{}') }
  try {
    await auth.employeeFetch('/api/exchange', { method: 'POST', body: new FormData() })
    assert.equal(calls[0].credentials, 'include')
    assert.equal(calls[0].headers.get('X-CSRF-Token'), 'unit-test-csrf')
    assert.equal(calls[0].headers.has('Content-Type'), false)
    globalThis.fetch = async () => new Response(JSON.stringify({ detail: { code: 'EMPLOYEE_AUTH_REQUIRED' } }), { status: 401 })
    await auth.employeeFetch('/api/news', {}, { redirect: false })
    assert.equal(state.currentEmployee.value, null); assert.equal(state.currentAdmin.value, null)
  } finally { globalThis.fetch = original; state.clearIdentity() }
})

test('logout from admin clears the same employee identity', async () => {
  const original = globalThis.fetch
  state.csrfToken.value = 'test-csrf'; state.currentEmployee.value = { id: 7 }; state.currentAdmin.value = { id: 8 }
  const admin = await server.ssrLoadModule('/src/utils/adminAuth.js')
  globalThis.fetch = async () => new Response('{}')
  try {
    await admin.logoutAdmin()
    assert.equal(state.currentEmployee.value, null); assert.equal(state.currentAdmin.value, null)
  } finally { globalThis.fetch = original; state.clearIdentity() }
})

test('employee editor renders password-only inputs and real account/permission fields', async () => {
  const { default: Editor } = await server.ssrLoadModule('/src/views/EmployeesAdminView.vue')
  const html = await renderToString(createSSRApp(Editor))
  assert.match(html, /员工账号管理/); assert.match(html, /项目维护权限/)
  assert.match(html, /type="password"/); assert.match(html, /autocomplete="new-password"/)
  assert.doesNotMatch(html, /公开注册|默认密码/)
})

test('one login response populates employee and admin roles without another credential request', async () => {
  const original = globalThis.fetch
  const calls = []
  state.csrfToken.value = 'before-login'
  globalThis.fetch = async (url, options) => {
    calls.push([url, options.method])
    return new Response(JSON.stringify({ id: 7, isAdmin: true, canEditProjects: true,
      mustChangePassword: false, admin: { id: 2, username: 'adminMO' }, csrfToken: 'after-login' }))
  }
  try {
    await auth.loginEmployee({ username: 'adminMO', password: 'synthetic-test-only' })
    assert.equal(calls.length, 1)
    assert.match(calls[0][0], /\/api\/employee\/login$/)
    assert.equal(state.currentEmployee.value.canEditProjects, true)
    assert.equal(state.currentAdmin.value.username, 'adminMO')
    assert.equal(state.csrfToken.value, 'after-login')
    assert.equal(await resolveAccess(route('admin', '/admin', true), { employee: async () => state.currentEmployee.value }), true)
    assert.equal(await resolveAccess(route('change-password', '/change-password'), { employee: async () => state.currentEmployee.value }), true)
  } finally { globalThis.fetch = original; state.clearIdentity() }
})
