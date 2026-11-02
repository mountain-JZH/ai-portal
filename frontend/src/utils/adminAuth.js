import { shallowRef } from 'vue'

import { API_BASE_URL } from '../config/api'

export const currentAdmin = shallowRef(null)

export async function fetchCurrentAdmin() {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    credentials: 'include',
  })

  if (response.status === 401) {
    currentAdmin.value = null
    return null
  }

  if (!response.ok) throw new Error(`Authentication check failed: ${response.status}`)

  currentAdmin.value = await response.json()
  return currentAdmin.value
}

export async function loginAdmin(credentials) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  })

  if (response.ok) currentAdmin.value = await response.json()

  return response
}

export async function logoutAdmin() {
  const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })

  currentAdmin.value = null
  return response
}

export async function adminFetch(input, init = {}) {
  const response = await fetch(input, {
    ...init,
    credentials: 'include',
  })

  if (response.status === 401) {
    currentAdmin.value = null

    if (window.location.pathname.startsWith('/admin')) {
      const redirect = `${window.location.pathname}${window.location.search}`
      window.location.assign(`/login?redirect=${encodeURIComponent(redirect)}`)
    }

    throw new Error('Authentication required')
  }

  return response
}
