<script setup>
import { onMounted, reactive, ref } from 'vue'
import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'

const employees = ref([]), loading = ref(true), busy = ref(false), error = ref(''), message = ref('')
const editing = ref(null), resetting = ref(null), temporaryPassword = ref('')
const empty = () => ({ username: '', name: '', department: '', isActive: true, canEditProjects: false, temporaryPassword: '' })
const form = reactive(empty())
async function request(path = '', init) {
  const response = await adminFetch(`${API_BASE_URL}/api/admin/employees${path}`, init)
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : '操作失败，请检查内容或重新验证管理员身份')
  return data
}
async function load() {
  loading.value = true
  try { employees.value = await request() } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
function edit(employee) {
  editing.value = employee.id
  Object.assign(form, empty(), { username: employee.username, name: employee.name, department: employee.department, isActive: employee.isActive, canEditProjects: employee.canEditProjects })
  message.value = ''; error.value = ''
}
function cancel() { editing.value = null; Object.assign(form, empty()) }
async function save() {
  if (busy.value) return
  busy.value = true; error.value = ''; message.value = ''
  try {
    const { username, temporaryPassword: password, ...fields } = form
    await request(editing.value ? `/${editing.value}` : '', {
      method: editing.value ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editing.value ? fields : { ...fields, username, temporaryPassword: password }),
    })
    cancel(); message.value = '账号已保存。初始密码请通过安全渠道交付，登录后可主动改密。'; await load()
  } catch (e) { error.value = e.message }
  finally { form.temporaryPassword = ''; busy.value = false }
}
async function reset() {
  if (busy.value || !resetting.value) return
  if (!window.confirm('确认重置密码并撤销该员工全部会话及管理员授权？')) return
  busy.value = true; error.value = ''; message.value = ''
  try {
    await request(`/${resetting.value.id}/reset-password`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ temporaryPassword: temporaryPassword.value }) })
    resetting.value = null; message.value = '密码已重置，旧会话已撤销，请使用新密码重新登录。'; await load()
  } catch (e) { error.value = e.message }
  finally { temporaryPassword.value = ''; busy.value = false }
}
onMounted(load)
</script>
<template>
  <section class="employees-admin">
    <h1>员工账号管理</h1><p>统一登录后自动识别权限；项目维护授权不授予系统管理权限。</p>
    <p v-if="error" role="alert">{{ error }}</p><p v-if="message" role="status">{{ message }}</p>
    <form class="employee-editor" @submit.prevent="save">
      <h2>{{ editing ? '编辑员工' : '添加员工' }}</h2>
      <label>登录账号<input v-model.trim="form.username" required :disabled="Boolean(editing) || busy" pattern="[a-zA-Z0-9][a-zA-Z0-9_.\-]{2,63}" autocomplete="off"></label>
      <label>姓名<input v-model="form.name" required maxlength="80" :disabled="busy"></label>
      <label>部门<input v-model="form.department" required maxlength="100" :disabled="busy"></label>
      <label v-if="!editing">一次性初始密码<input v-model="form.temporaryPassword" type="password" autocomplete="new-password" required minlength="12" maxlength="128" :disabled="busy"></label>
      <label class="employee-check"><input v-model="form.isActive" type="checkbox" :disabled="busy">启用账号（停用立即撤销全部会话）</label>
      <label class="employee-check"><input v-model="form.canEditProjects" type="checkbox" :disabled="busy">项目维护权限</label>
      <div><button :disabled="busy">{{ busy ? '保存中…' : '保存账号' }}</button> <button v-if="editing" type="button" :disabled="busy" @click="cancel">取消编辑</button></div>
    </form>
    <form v-if="resetting" class="employee-editor" @submit.prevent="reset">
      <h2>重置 {{ resetting.username }} 的临时密码</h2>
      <label>新临时密码<input v-model="temporaryPassword" type="password" autocomplete="new-password" required minlength="12" maxlength="128"></label>
      <div><button :disabled="busy">重置并撤销会话</button> <button type="button" :disabled="busy" @click="resetting = null; temporaryPassword = ''">取消</button></div>
    </form>
    <p v-if="loading" role="status">正在读取员工账号…</p>
    <div v-else class="employee-table"><table><thead><tr><th>账号 / 姓名</th><th>部门</th><th>状态 / 权限</th><th>最近登录</th><th>操作</th></tr></thead><tbody>
      <tr v-for="employee in employees" :key="employee.id"><td>{{ employee.username }}<br>{{ employee.name }}</td><td>{{ employee.department }}</td><td>{{ employee.isActive ? '启用' : '停用' }} · {{ employee.isAdmin ? '管理员' : employee.canEditProjects ? '可维护项目' : '普通员工' }}</td><td>{{ employee.lastLoginAt ? new Date(employee.lastLoginAt).toLocaleString('zh-CN') : '尚未登录' }}</td><td><button @click="edit(employee)">编辑</button> <button @click="resetting = employee; temporaryPassword = ''">重置密码</button></td></tr>
      <tr v-if="!employees.length"><td colspan="5">暂无员工账号</td></tr>
    </tbody></table></div>
  </section>
</template>
<style scoped>
.employees-admin { color: #22292c; max-width: 1100px; }
.employees-admin h1 { font-size: 28px; }
.employees-admin p { line-height: 1.7; }
.employee-editor { display: grid; gap: 16px; padding: 24px; background: #fff; border: 1px solid #e5e8e9; border-radius: 12px; margin: 24px 0; max-width: 620px; }
.employee-editor h2 { margin: 0; font-size: 19px; }
.employee-editor label { display: grid; gap: 8px; font-size: 14px; }
.employee-editor input:not([type=checkbox]) { width: 100%; min-height: 42px; border: 1px solid #ccd1d3; border-radius: 6px; padding: 8px 12px; box-sizing: border-box; }
.employee-editor .employee-check { display: flex; align-items: center; }
button { min-height: 38px; padding: 8px 14px; border: 1px solid #ccd1d3; border-radius: 6px; background: #fff; color: #22292c; cursor: pointer; }
.employee-editor button[type=submit], .employee-editor button:not([type]) { background: #f7b334; border-color: #f7b334; }
button:disabled { opacity: .6; cursor: wait; }
:focus-visible { outline: 2px solid #6d5b55; outline-offset: 2px; }
.employee-table { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; background: #fff; }
th, td { padding: 14px; border-bottom: 1px solid #e5e8e9; text-align: left; font-size: 14px; }
td button { white-space: nowrap; }
@media(max-width:600px) { .employee-editor { padding: 16px; } }
</style>
