const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
const defaultApiBaseUrl = import.meta.env.DEV
  ? 'http://127.0.0.1:8000'
  : '/api'
const normalizedApiBaseUrl = (configuredApiBaseUrl || defaultApiBaseUrl).replace(
  /\/+$/,
  '',
)

// Existing request paths already begin with /api. A production base of /api
// therefore maps to the current origin without producing /api/api/....
export const API_BASE_URL = normalizedApiBaseUrl === '/api' ? '' : normalizedApiBaseUrl
