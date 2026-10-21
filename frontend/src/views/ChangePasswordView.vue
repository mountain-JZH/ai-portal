<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { changeEmployeePassword, logoutEmployee, safeReturnPath } from '../utils/employeeAuth'
import '../assets/employee-login.css'

const route = useRoute(), router = useRouter()
const currentPassword = ref(''), newPassword = ref(''), confirmPassword = ref('')
const error = ref(''), busy = ref(false)
async function save() {
  if (busy.value) return
  error.value = ''
  if (newPassword.value !== confirmPassword.value) { error.value = '两次新密码输入不同'; return }
  busy.value = true
  try {
    const response = await changeEmployeePassword({ currentPassword: currentPassword.value, newPassword: newPassword.value })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      error.value = typeof data?.detail === 'string' ? data.detail : '修改失败，请重试'
      return
    }
    currentPassword.value = ''; newPassword.value = ''; confirmPassword.value = ''
    await router.replace(safeReturnPath(route.query.redirect))
  } catch { error.value = '修改失败，请检查网络后重试' }
  finally { busy.value = false }
}
async function exit() {
  try { await logoutEmployee(); await router.replace('/login') }
  catch { error.value = '退出失败，请重试' }
}
</script>
<template>
  <main class="employee-login-page">
    <section class="employee-login-brand"><div class="employee-wordmark">AI <span>PORTAL</span></div><h1>A fresh<br>start.</h1><p>信息运维部智能助手平台</p></section>
    <section class="employee-login-panel">
      <form class="employee-auth-form" @submit.prevent="save">
        <h2>修改密码</h2><p class="employee-auth-hint">可主动设置 12–128 位新密码，保存后其他旧会话将失效。</p>
        <label>当前密码<input v-model="currentPassword" type="password" autocomplete="current-password" required maxlength="1000"></label>
        <label>新密码<input v-model="newPassword" type="password" autocomplete="new-password" required minlength="12" maxlength="128"></label>
        <label>确认新密码<input v-model="confirmPassword" type="password" autocomplete="new-password" required minlength="12" maxlength="128"></label>
        <p v-if="error" class="employee-auth-error" role="alert">{{ error }}</p>
        <button class="employee-auth-primary" :disabled="busy">{{ busy ? '保存中…' : '保存并进入平台' }}</button>
        <button type="button" :disabled="busy" @click="exit">退出员工登录</button>
      </form>
    </section>
  </main>
</template>
