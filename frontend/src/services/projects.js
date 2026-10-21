import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'
import { employeeFetch } from '../utils/employeeAuth'

const root = `${API_BASE_URL}/api/admin/projects`

async function request(path = '', options = {}, employee = false) {
  const response = await (employee ? employeeFetch : adminFetch)(
    `${employee ? `${API_BASE_URL}/api/projects` : root}${path}`,
    options,
  )
  const result = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(
      typeof result.detail === 'string'
        ? result.detail
        : result.detail?.message || `请求失败（${response.status}），请重试。`,
    )
    error.status = response.status
    throw error
  }
  return result
}

export function loadEmployeeProjects(filters = {}, signal) {
  const query = new URLSearchParams()
  for (const [name, value] of Object.entries(filters)) {
    for (const item of Array.isArray(value) ? value : [value]) {
      if (item !== '' && item != null && item !== false) query.append(name, String(item))
    }
  }
  return request(`?${query}`, { signal }, true)
}

export function loadEmployeeProjectDetail(id, signal) {
  return request(`/${encodeURIComponent(id)}`, { signal }, true)
}

export function saveEmployeeProject(id, version, changes) {
  return request(
    id ? `/${encodeURIComponent(id)}` : '',
    {
      method: id ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(id ? { version, changes } : changes),
    },
    true,
  )
}

export function loadProjectHistory(id, field = '', offset = 0, signal) {
  return request(
    `/${encodeURIComponent(id)}/history?${new URLSearchParams({ field, offset, limit: 50 })}`,
    { signal },
    true,
  )
}

export function loadProjects(filters = {}, signal) {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value))
  return request(`?${query}`, { signal })
}
export function loadProjectDetail(id) {
  return request(`/${id}`)
}
export function previewProjects(file) {
  const form = new FormData()
  form.append('file', file)
  return request('/imports/preview', { method: 'POST', body: form })
}
export function confirmProjects(token) {
  return request('/imports/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  })
}
export function cancelProjectPreview(token) {
  return request(`/imports/preview/${encodeURIComponent(token)}`, { method: 'DELETE' })
}
