<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'

const router = useRouter()
const auth = useAuth()
const username = ref('')
const password = ref('')

async function submit() {
  await auth.login(username.value, password.value)
  await auth.fetchProfile()
  router.push('/dashboard')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <router-link to="/" class="auth-back">← 返回</router-link>
      <h1>欢迎回来</h1>
      <p class="auth-desc">登录以获取个性化膳食建议</p>
      <form @submit.prevent="submit">
        <label>用户名</label>
        <input v-model="username" class="inp" placeholder="输入用户名" autocomplete="username" required />
        <label>密码</label>
        <input v-model="password" class="inp" type="password" placeholder="输入密码" autocomplete="current-password" required />
        <p v-if="auth.err" class="auth-err">{{ auth.err }}</p>
        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" :disabled="auth.loading">
          <span v-if="auth.loading" class="spinner"></span>
          <span v-else>登 录</span>
        </button>
      </form>
      <p class="auth-link">没有账号？<router-link to="/register">立即注册</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { min-height: calc(100vh - 56px); display: flex; align-items: center; justify-content: center; background: var(--c-bg) }
.auth-card { width: 400px; max-width: 90vw; background: var(--c-surface); border-radius: var(--r-lg); padding: 44px 36px; border: 1px solid var(--c-border-light); box-shadow: var(--shadow-lg) }
.auth-back { font-size: 13px; color: var(--c-ink-muted); display: inline-block; margin-bottom: 24px }
.auth-back:hover { color: var(--c-primary) }
h1 { font: 700 26px var(--font-display); letter-spacing: .02em }
.auth-desc { font-size: 14px; color: var(--c-ink-muted); margin-bottom: 28px }
form { display: flex; flex-direction: column; gap: 6px }
label { font-size: 13px; font-weight: 500; color: var(--c-ink-soft); margin-top: 4px }
.auth-err { font-size: 13px; color: var(--c-danger); text-align: center }
.auth-link { text-align: center; margin-top: 22px; font-size: 14px; color: var(--c-ink-muted) }
</style>
