import { API_BASE_URL } from '../config/api'
import { clearIdentity, csrfToken, currentAdmin, currentEmployee } from './authState'

export { currentEmployee } from './authState'
let csrfPending
const channel = typeof window !== 'undefined' && typeof BroadcastChannel !== 'undefined'
  ? new BroadcastChannel('ai-portal-identity') : null
if (channel) channel.onmessage = () => { clearIdentity(); window.location.reload() }

export function safeReturnPath(value, fallback = '/') {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') &&
    !value.includes('\\') && !Array.from(value).some((char) => char.charCodeAt(0) <= 32) && !/^\/(?:login|admin\/login|change-password)(?:[/?#]|$)/.test(value)
    ? value : fallback
}

async function ensureCsrf() {
  if (csrfToken.value) return csrfToken.value
  if (!csrfPending) csrfPending = fetch(`${API_BASE_URL}/api/employee/csrf`, { credentials: 'include' })
    .then(async (response) => {
      if (!response.ok) throw new Error('无法建立安全登录会话，请刷新重试')
      csrfToken.value = (await response.json()).csrfToken
      return csrfToken.value
    }).finally(() => { csrfPending = null })
  return csrfPending
}

export async function employeeFetch(input, init = {}, { redirect = true } = {}) {
  const method = (init.method || 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers.set('X-CSRF-Token', await ensureCsrf())
  const response = await fetch(input, { ...init, headers, credentials: 'include' })
  if (response.status === 401 || response.status === 403) {
    const detail = (await response.clone().json().catch(() => null))?.detail
    if (detail?.code === 'EMPLOYEE_AUTH_REQUIRED') {
      clearIdentity()
      if (redirect && typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        const target = safeReturnPath(`${window.location.pathname}${window.location.search}`)
        window.location.replace(`/login?redirect=${encodeURIComponent(target)}`)
      }
    } else if (detail?.code === 'PASSWORD_CHANGE_REQUIRED' && redirect && typeof window !== 'undefined') {
      window.location.replace('/change-password')
    }
  }
  return response
}

export async function fetchCurrentEmployee() {
  const response = await employeeFetch(`${API_BASE_URL}/api/employee/me`, {}, { redirect: false })
  if (response.status === 401) { clearIdentity(); return null }
  if (!response.ok) throw new Error('登录状态检查失败，请稍后重试')
  const data = await response.json()
  currentAdmin.value = data.isAdmin ? data.admin : null
  csrfToken.value = data.csrfToken
  currentEmployee.value = data
  return data
}

export async function loginEmployee(credentials) {
  const response = await employeeFetch(`${API_BASE_URL}/api/employee/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(credentials),
  }, { redirect: false })
  if (response.ok) {
    const data = await response.clone().json()
    currentAdmin.value = data.isAdmin ? data.admin : null
    currentEmployee.value = data
    csrfToken.value = data.csrfToken
    channel?.postMessage('changed')
  }
  return response
}

export async function changeEmployeePassword(payload) {
  const response = await employeeFetch(`${API_BASE_URL}/api/employee/password`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  })
  if (response.ok) {
    const data = await response.clone().json()
    currentEmployee.value = data
    currentAdmin.value = data.isAdmin ? data.admin : null
    csrfToken.value = data.csrfToken
    channel?.postMessage('changed')
  }
  return response
}

export async function logoutEmployee() {
  const response = await employeeFetch(`${API_BASE_URL}/api/employee/logout`, { method: 'POST' })
  if (!response.ok) throw new Error('退出未完成，请重试')
  clearIdentity()
  channel?.postMessage('changed')
}
