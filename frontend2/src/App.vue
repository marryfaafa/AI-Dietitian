<script setup lang="ts">
import { useAuth } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
const auth = useAuth()
const router = useRouter()
const route = useRoute()
</script>

<template>
  <div class="app-root">
    <!-- 登录后顶部导航 -->
    <header v-if="auth.isLoggedIn && route.name !== 'Home'" class="topbar">
      <div class="topbar-inner">
        <router-link to="/dashboard" class="tb-logo">膳养<span class="tb-sub">/ 智能膳食健康顾问</span></router-link>
        <nav class="tb-nav">
          <router-link to="/dashboard" :class="{ on: route.name === 'Dashboard' }">概览</router-link>
          <router-link to="/profile" :class="{ on: route.name === 'Profile' }">画像</router-link>
          <router-link to="/report" :class="{ on: route.name === 'Report' }">报告</router-link>
          <router-link to="/meals" :class="{ on: route.name === 'Meals' }">配餐</router-link>
          <router-link to="/chat" :class="{ on: route.name === 'Chat' }">咨询</router-link>
        </nav>
        <div class="tb-right">
          <span>{{ auth.name }}</span>
          <button class="tb-btn" @click="auth.logout(); router.push('/')">退出</button>
        </div>
      </div>
    </header>

    <!-- 内容区（首页无边距，其他有） -->
    <main v-if="route.name === 'Home'">
      <router-view />
    </main>
    <main v-else class="page-wrap">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-root { min-height: 100vh; display: flex; flex-direction: column }
.topbar { border-bottom: 1px solid var(--c-border); background: rgba(255,255,255,.85); backdrop-filter: blur(16px); position: sticky; top: 0; z-index: 100 }
.topbar-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; padding: 0 32px; height: 56px }
.tb-logo { font: 900 18px var(--font-display); color: var(--c-primary); letter-spacing: .04em }
.tb-sub { font-size: 12px; font-weight: 400; color: var(--c-ink-muted) }
.tb-nav { display: flex; gap: 2px; margin-left: 32px }
.tb-nav a { padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; color: var(--c-ink-soft); transition: all .15s }
.tb-nav a:hover { background: var(--c-primary-bg); color: var(--c-primary) }
.tb-nav a.on { background: var(--c-primary); color: white }
.tb-right { margin-left: auto; display: flex; align-items: center; gap: 16px; font-size: 13px; color: var(--c-ink-soft) }
.tb-btn { font-size: 12px; color: var(--c-ink-muted); background: none; padding: 4px 8px; border-radius: 4px }
.tb-btn:hover { color: var(--c-danger); background: var(--c-danger-bg) }
.page-wrap { max-width: 1200px; margin: 0 auto; padding: 32px 24px; width: 100% }
@media(max-width:768px){ .tb-nav{ display:none } .topbar-inner{ padding:0 16px } }
</style>
