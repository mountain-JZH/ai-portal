import { currentEmployee } from './authState'

// Never assign anonymous legacy data to whichever employee happens to log in first.
export function personalKey(key) {
  const id = currentEmployee.value?.id
  return Number.isSafeInteger(id) && id > 0 ? `${key}:employee:${id}` : null
}

export const personalStorage = {
  getItem(key) { const scoped = personalKey(key); return scoped ? localStorage.getItem(scoped) : null },
  setItem(key, value) { const scoped = personalKey(key); if (scoped) localStorage.setItem(scoped, value) },
  removeItem(key) { const scoped = personalKey(key); if (scoped) localStorage.removeItem(scoped) },
}
