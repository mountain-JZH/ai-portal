import { shallowRef } from 'vue'

export const currentEmployee = shallowRef(null)
export const currentAdmin = shallowRef(null)
export const csrfToken = shallowRef('')

export function clearIdentity() {
  currentEmployee.value = null
  currentAdmin.value = null
  csrfToken.value = ''
}
