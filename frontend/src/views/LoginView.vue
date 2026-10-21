<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { currentEmployee, loginEmployee, safeReturnPath } from '../utils/employeeAuth'
import '../assets/employee-login.css'

const route = useRoute()
const router = useRouter()
const username = ref('')
const password = ref('')
const submitting = ref(false)
const errorMessage = ref(route.query.unavailable ? '登录状态检查暂时不可用，请重试。' : '')
async function submitLogin() {
  if (submitting.value) return
  submitting.value = true
  errorMessage.value = ''
  try {
    const response = await loginEmployee({ username: username.value, password: password.value })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      errorMessage.value = typeof data?.detail === 'string' ? data.detail : '验证失败，请检查账号和密码后重试'
      return
    }
    password.value = ''
    const target = safeReturnPath(route.query.redirect, currentEmployee.value?.isAdmin ? '/admin' : '/')
    await router.replace(target)
  } catch { errorMessage.value = '登录服务暂时不可用，请稍后重试' }
  finally { submitting.value = false }
}
</script>

<template>
  <main class="employee-login-page">
    <section class="employee-login-brand" aria-label="AI Portal">
      <div class="employee-wordmark">AI <span>PORTAL</span></div>
      <h1>Make work.<br>Flow better.</h1>
      <p>信息运维部智能助手平台</p>
    </section>
    <section class="employee-login-panel">
      <form class="employee-auth-form" @submit.prevent="submitLogin">
        <p class="employee-auth-eyebrow">内部工作平台</p>
        <h2>欢迎回来</h2>
        <p class="employee-auth-hint">使用平台账号登录，系统自动识别访问权限，无需注册。</p>
        <label>账号<input v-model.trim="username" autocomplete="username" maxlength="100" required></label>
        <label>密码<input v-model="password" type="password" autocomplete="current-password" maxlength="1000" required></label>
        <p v-if="errorMessage" class="employee-auth-error" role="alert">{{ errorMessage }}</p>
        <button class="employee-auth-primary" :disabled="submitting">{{ submitting ? '登录中…' : '登录' }}</button>
        <p class="employee-auth-hint">账号或密码需要重置？请联系平台管理员。</p>
      </form>
    </section>
  </main>
</template>
