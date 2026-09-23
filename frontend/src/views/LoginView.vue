<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { loginAdmin } from '../utils/adminAuth'

const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const errorMessage = ref('')

function getRedirectTarget() {
  const target = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  return target.startsWith('/admin') ? target : '/admin'
}

async function submitLogin() {
  if (submitting.value) return

  submitting.value = true
  errorMessage.value = ''

  try {
    const response = await loginAdmin({
      username: username.value,
      password: password.value,
    })

    if (response.status === 401) {
      errorMessage.value = '用户名或密码错误'
      return
    }

    if (!response.ok) {
      errorMessage.value = '登录服务暂时不可用，请稍后重试'
      return
    }

    await router.replace(getRedirectTarget())
  } catch {
    errorMessage.value = '登录服务暂时不可用，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card" aria-labelledby="login-title">
      <div class="login-brand" aria-hidden="true">AI</div>
      <p class="login-platform">信息运维部智能助手平台</p>
      <h1 id="login-title">管理后台登录</h1>

      <form class="login-form" @submit.prevent="submitLogin">
        <label>
          <span>用户名</span>
          <input
            v-model.trim="username"
            type="text"
            name="username"
            autocomplete="username"
            maxlength="100"
            required
          />
        </label>

        <label>
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            name="password"
            autocomplete="current-password"
            maxlength="1000"
            required
          />
        </label>

        <p v-if="errorMessage" class="login-error" role="alert">
          {{ errorMessage }}
        </p>

        <button type="submit" :disabled="submitting">
          {{ submitting ? '登录中…' : '登录' }}
        </button>
      </form>

      <RouterLink to="/" class="portal-link">← 返回门户</RouterLink>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 48px 16px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 50% 0, rgba(91, 91, 214, 0.12), transparent 42%),
    var(--color-bg);
}

.login-card {
  width: min(100%, 400px);
  padding: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.login-brand {
  width: 44px;
  height: 44px;
  margin-bottom: 18px;
  display: grid;
  place-items: center;
  border-radius: var(--radius-md);
  background: linear-gradient(145deg, #536fd9, #655ce7);
  color: #fff;
  font-weight: 700;
}

.login-platform {
  margin: 0 0 6px;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 600;
}

h1 {
  margin: 0;
  font-size: 26px;
}

.login-form {
  margin-top: 28px;
  display: grid;
  gap: 18px;
}

label {
  display: grid;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
}

input {
  width: 100%;
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--color-text);
}

input:focus {
  border-color: var(--color-primary);
}

.login-error {
  margin: 0;
  color: #bd3e4b;
  font-size: 13px;
}

button {
  min-height: 44px;
  border: 0;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  cursor: pointer;
  font-weight: 700;
}

button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.portal-link {
  margin-top: 24px;
  display: inline-flex;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 13px;
}

.portal-link:hover {
  color: var(--color-primary);
}

@media (max-width: 500px) {
  .login-page {
    padding: 24px 16px;
  }

  .login-card {
    padding: 28px 22px;
  }
}
</style>
