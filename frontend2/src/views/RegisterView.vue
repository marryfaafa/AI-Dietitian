<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'

const router = useRouter()
const auth = useAuth()
const pname = ref('')
const username = ref('')
const password = ref('')
const confirm = ref('')

async function submit() {
  if (password.value !== confirm.value) { auth.err = '两次密码不一致'; return }
  await auth.register(username.value, password.value, pname.value || username.value)
  router.push('/profile')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <router-link to="/" class="auth-back">← 返回</router-link>
      <h1>创建账号</h1>
      <p class="auth-desc">开启个性化健康膳食之旅</p>
      <form @submit.prevent="submit">
        <label>昵称</label><input v-model="pname" class="inp" placeholder="如何称呼您" />
        <label>用户名</label><input v-model="username" class="inp" placeholder="用于登录" required />
        <label>密码</label><input v-model="password" class="inp" type="password" minlength="4" placeholder="至少4个字符" required />
        <label>确认密码</label><input v-model="confirm" class="inp" type="password" placeholder="再次输入" required />
        <p v-if="auth.err" class="auth-err">{{ auth.err }}</p>
        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" :disabled="auth.loading">
          {{ auth.loading ? '注册中...' : '注 册' }}
        </button>
      </form>
      <p class="auth-link">已有账号？<router-link to="/login">登录</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { min-height: calc(100vh - 56px); display: flex; align-items: center; justify-content: center; background: var(--c-bg) }
.auth-card { width: 400px; max-width: 90vw; background: var(--c-surface); border-radius: var(--r-lg); padding: 40px 36px; border: 1px solid var(--c-border-light); box-shadow: var(--shadow-lg) }
.auth-back { font-size: 13px; color: var(--c-ink-muted); display: inline-block; margin-bottom: 20px }
h1 { font: 700 26px var(--font-display) }
.auth-desc { font-size: 14px; color: var(--c-ink-muted); margin-bottom: 24px }
form { display: flex; flex-direction: column; gap: 4px }
label { font-size: 13px; font-weight: 500; color: var(--c-ink-soft); margin-top: 2px }
.auth-err { font-size: 13px; color: var(--c-danger); text-align: center }
.auth-link { text-align: center; margin-top: 20px; font-size: 14px; color: var(--c-ink-muted) }
</style>
