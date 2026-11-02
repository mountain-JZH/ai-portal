import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'
import { safeUrl, validateExchangeFields } from '../utils/exchangeDiscovery'

export function resolveExchangeImage(path) {
  if (typeof path !== 'string') return ''
  if (/^\/uploads\/exchange\/[a-f0-9]{32}\.webp$/.test(path)) return `${API_BASE_URL}${path}`
  return safeUrl(path)
}

function resourceFromApi(resource) {
  if (
    !Number.isSafeInteger(resource?.id) ||
    resource.id < 1 ||
    typeof resource.title !== 'string' ||
    !Array.isArray(resource.tags)
  ) {
    throw new Error('服务器返回了无效的分享数据，请重新读取。')
  }
  return {
    ...resource,
    displayNumber: String(resource.id).padStart(3, '0'),
    imageUrl: resolveExchangeImage(resource.imageUrl),
    externalUrl: safeUrl(resource.externalUrl),
  }
}

async function requestJson(path, init = {}, authenticated = false) {
  let response
  try {
    response = await (authenticated ? adminFetch : fetch)(`${API_BASE_URL}${path}`, {
      ...init,
      ...(authenticated ? {} : { credentials: 'omit' }),
    })
  } catch (error) {
    if (error.message === 'Authentication required') throw error
    throw new Error('网络连接失败，请检查连接后重试。', { cause: error })
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const error = new Error(
      typeof data?.detail === 'string' ? data.detail : `请求失败（${response.status}）`,
    )
    error.status = response.status
    throw error
  }
  if (data === null) throw new Error('服务器响应无效，请重试。')
  return data
}

export async function loadExchangeResources() {
  const items = await requestJson('/api/exchange?limit=200')
  if (!Array.isArray(items)) throw new Error('服务器资源列表无效。')
  return items.map(resourceFromApi)
}

export async function submitExchangeResource(fields) {
  const payload = validateExchangeFields(fields)
  const body = new FormData()
  body.append('payload', JSON.stringify(payload))
  if (fields.imageBlob) body.append('file', fields.imageBlob, 'exchange-cover.webp')
  return resourceFromApi(await requestJson('/api/exchange', { method: 'POST', body }))
}

export async function loadAdminExchangeResources(page = 1) {
  const data = await requestJson(`/api/admin/exchange?limit=20&offset=${(page - 1) * 20}`, {}, true)
  if (!Array.isArray(data.items) || !Number.isSafeInteger(data.total))
    throw new Error('服务器管理列表无效。')
  return { items: data.items.map(resourceFromApi), total: data.total }
}

export async function loadAdminExchangeDetail(id) {
  return resourceFromApi(await requestJson(`/api/admin/exchange/${id}`, {}, true))
}

export async function deleteExchangeResource(id) {
  return requestJson(`/api/admin/exchange/${id}`, { method: 'DELETE' }, true)
}
