import { API_BASE_URL } from '../config/api'
import { currentAdmin } from './authState'
import { employeeFetch, loginEmployee, logoutEmployee } from './employeeAuth'
export { currentAdmin } from './authState'

export async function fetchCurrentAdmin() {
  const response = await employeeFetch(`${API_BASE_URL}/api/auth/me`, {
    credentials: 'include',
  })

  if (response.status === 401 || response.status === 403) {
    currentAdmin.value = null
    return null
  }

  if (!response.ok) throw new Error(`Authentication check failed: ${response.status}`)

  currentAdmin.value = await response.json()
  return currentAdmin.value
}

export async function loginAdmin(credentials) {
  return loginEmployee(credentials)
}

export async function logoutAdmin() {
  return logoutEmployee()
}

export async function adminFetch(input, init = {}) {
  const response = await employeeFetch(input, {
    ...init,
    credentials: 'include',
  })

  if (response.status === 401) {
    currentAdmin.value = null

    const detail = (await response.clone().json().catch(() => null))?.detail
    if (typeof window !== 'undefined' && detail?.code !== 'EMPLOYEE_AUTH_REQUIRED' && window.location.pathname.startsWith('/admin')) {
      const redirect = `${window.location.pathname}${window.location.search}`
      window.location.assign(`/login?redirect=${encodeURIComponent(redirect)}`)
    }

    throw new Error('Authentication required')
  }

  return response
}
