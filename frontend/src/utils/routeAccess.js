import { fetchCurrentEmployee, safeReturnPath } from './employeeAuth'

export async function resolveAccess(to, checks = { employee: fetchCurrentEmployee }) {
  let employee
  try { employee = await checks.employee() } catch {
    return to.name === 'login' ? true : { name: 'login', query: { redirect: to.fullPath, unavailable: '1' } }
  }
  if (!employee) return to.name === 'login' ? true : { name: 'login', query: { redirect: to.fullPath } }
  if (to.name === 'login') return safeReturnPath(to.query.redirect, employee.isAdmin ? '/admin' : '/')
  if (to.matched.some((record) => record.meta.requiresAdmin) && !employee.isAdmin)
    return { name: 'home', query: { permission: 'admin-required' } }
  return true
}
