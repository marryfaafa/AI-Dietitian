<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuth } from '@/stores/auth'
import { api } from '@/api'

const auth = useAuth()
const report = ref('')
const stats = ref<any>({})
const meals = ref<any[]>([])

onMounted(async () => {
  try { const r = await api.getReport(); report.value = r.report; stats.value = r.stats; meals.value = r.recent_meals || [] } catch { /* */ }
})
</script>

<template>
  <div class="page">
    <div class="welcome">
      <div>
        <h1>你好，{{ auth.name || '膳友' }}</h1>
        <p>今日膳食适配度</p>
      </div>
      <div class="score">{{ (stats.avg_rating * 20 || 85).toFixed(0) }}<small>分</small></div>
    </div>

    <div class="grid2">
      <div class="box">
        <h3>健康概要</h3>
        <pre class="txt" v-if="report">{{ report }}</pre>
        <p v-else class="muted">请先完善健康画像</p>
      </div>
      <div class="box">
        <h3>近期用餐</h3>
        <div v-if="!meals.length" class="muted">暂无记录</div>
        <div v-for="m in meals.slice(0,5)" :key="m.recipe_name" class="mr">
          <span>{{ m.recipe_name }}</span>
          <span class="muted">{{ m.meal_type }} &middot; {{ m.created_at?.slice(0,10) }}</span>
        </div>
      </div>
    </div>

    <div class="quick">
      <router-link to="/profile" class="q-card"><span>🧬</span><strong>完善画像</strong><small>更新体质信息</small></router-link>
      <router-link to="/meals" class="q-card"><span>🍽️</span><strong>今日配餐</strong><small>AI 智能推荐</small></router-link>
      <router-link to="/chat" class="q-card"><span>💬</span><strong>膳食咨询</strong><small>个性化建议</small></router-link>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 24px }
.welcome { display: flex; align-items: center; justify-content: space-between; padding: 36px; border-radius: var(--r-lg); background: linear-gradient(135deg, var(--c-primary-bg), rgba(184,155,114,.05)); border: 1px solid var(--c-border-light) }
.welcome h1 { font: 700 26px var(--font-display) }
.welcome p { font-size: 14px; color: var(--c-ink-muted); margin-top: 4px }
.score { width: 72px; height: 72px; border-radius: 50%; background: var(--c-primary); color: white; display: flex; align-items: center; justify-content: center; font: 900 26px var(--font-display); flex-direction: column }
.score small { font-size: 10px; font-weight: 400; opacity: .7 }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px }
.box { background: var(--c-surface); border: 1px solid var(--c-border-light); border-radius: var(--r-lg); padding: 24px }
.box h3 { font: 600 15px var(--font-display); padding-bottom: 12px; margin-bottom: 16px; border-bottom: 2px solid var(--c-border-light) }
.txt { white-space: pre-wrap; font-size: 13px; line-height: 1.8; color: var(--c-ink-soft) }
.mr { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--c-border-light); font-size: 14px }
.mr:last-child { border: none }
.quick { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px }
.q-card { background: var(--c-surface); border: 1px solid var(--c-border-light); border-radius: var(--r); padding: 24px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; text-decoration: none; color: var(--c-ink); transition: all .2s }
.q-card:hover { border-color: var(--c-primary); transform: translateY(-2px); box-shadow: var(--shadow) }
.q-card span { font-size: 28px }
.q-card strong { font: 600 15px var(--font-display) }
.q-card small { font-size: 12px; color: var(--c-ink-muted) }
.muted { color: var(--c-ink-muted); font-size: 14px; padding: 12px 0 }
@media(max-width:768px){ .grid2,.quick{ grid-template-columns:1fr } }
</style>
