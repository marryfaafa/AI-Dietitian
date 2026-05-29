<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'

const plans = ref<any[]>([])
const summary = ref('')
const loading = ref(false)

const candidates = [
  { name:"小米粥",nodeId:"101",category:"早餐",ingredient_names:["小米","水"],ingredients:["小米","水"] },
  { name:"蒸鸡蛋羹",nodeId:"102",category:"早餐",ingredient_names:["鸡蛋","水"],ingredients:["鸡蛋","水"] },
  { name:"清蒸鲈鱼",nodeId:"103",category:"水产",ingredient_names:["鲈鱼","葱"],ingredients:["鲈鱼","葱"] },
  { name:"蒜蓉西兰花",nodeId:"104",category:"素菜",ingredient_names:["西兰花","蒜"],ingredients:["西兰花","蒜"] },
  { name:"红烧豆腐",nodeId:"105",category:"素菜",ingredient_names:["豆腐","豆瓣酱"],ingredients:["豆腐","豆瓣酱"] },
  { name:"冬瓜薏米汤",nodeId:"106",category:"汤类",ingredient_names:["冬瓜","薏米"],ingredients:["冬瓜","薏米"] },
  { name:"凉拌黄瓜",nodeId:"107",category:"素菜",ingredient_names:["黄瓜"],ingredients:["黄瓜"] },
  { name:"西红柿炒蛋",nodeId:"108",category:"素菜",ingredient_names:["番茄","鸡蛋"],ingredients:["番茄","鸡蛋"] },
  { name:"芹菜炒牛肉",nodeId:"109",category:"荤菜",ingredient_names:["芹菜","牛肉"],ingredients:["芹菜","牛肉"] },
  { name:"燕麦粥",nodeId:"110",category:"早餐",ingredient_names:["燕麦"],ingredients:["燕麦"] },
]

async function plan(type: string) {
  loading.value = true
  try {
    if (type === 'daily') {
      const r = await api.planDaily({ candidates, date: new Date().toISOString().slice(0,10) })
      plans.value = [{ ...r, meals: r.meals || [] }]; summary.value = r.summary || ''
    } else {
      const r = await api.planWeekly({ candidates, days: 7 })
      plans.value = r.daily_plans || []; summary.value = r.overall_summary || ''
    }
  } catch (e: any) { summary.value = '失败: ' + e.message }
  loading.value = false
}

const logged = ref(new Set<string>()) // 已记录的餐食

async function logMeal(name: string, mealType: string, nodeId: string) {
  try {
    await api.logMeal({ recipe_name: name, meal_type: mealType, recipe_node_id: nodeId, rating: 4 })
    logged.value.add(name + mealType)
  } catch { /* */ }
}

const icons: Record<string,string> = { '早餐':'🌅', '午餐':'☀️', '晚餐':'🌙' }
</script>

<template>
  <div>
    <div class="mb">
      <div><h2 class="pg-title">智能配餐规划</h2><p class="sub">基于你的体质与健康，AI 定制膳食方案</p></div>
      <div class="mb-btns"><button class="btn btn-primary" :disabled="loading" @click="plan('daily')">今日配餐</button><button class="btn btn-outline" :disabled="loading" @click="plan('weekly')">一周配餐</button></div>
    </div>

    <div v-if="loading" style="display:flex;align-items:center;gap:10px;color:var(--c-ink-muted)"><div class="spinner"></div>AI 规划中...</div>
    <p v-if="summary" class="sm">{{ summary }}</p>

    <div v-for="(d,di) in plans" :key="di" class="day">
      <h4>{{ d.date || '第'+(di+1)+'天' }} <span v-if="d.total_score">&middot; {{ (d.total_score*100).toFixed(0) }}分</span></h4>
      <div v-for="m in (d.meals||[])" :key="m.meal_type+m.recipe_name" class="meal">
        <span class="mi">{{ icons[m.meal_type]||'🍽️' }}</span>
        <div class="mn"><b>{{ m.meal_type }}</b> {{ m.recipe_name }}<small>{{ m.reason || '' }}</small></div>
        <span class="ms">+{{ (m.compliance_score*100).toFixed(0) }}</span>
        <button v-if="!logged.has(m.recipe_name + m.meal_type)" class="btn-log" @click="logMeal(m.recipe_name, m.meal_type, m.recipe_node_id)">记录用餐</button>
        <span v-else class="logged-done">已记录</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pg-title { font: 700 26px var(--font-display) }
.sub { font-size: 14px; color: var(--c-ink-muted); margin-top: 4px }
.mb { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 24px }
.mb-btns { display: flex; gap: 10px }
.sm { font-size: 14px; color: var(--c-ink-soft); background: var(--c-primary-bg); padding: 14px; border-radius: var(--r-sm); margin-bottom: 16px; line-height: 1.7 }
.day { margin-bottom: 8px }
.day h4 { font: 600 15px var(--font-display); padding-bottom: 8px; border-bottom: 1px solid var(--c-border-light); margin-bottom: 10px }
.day h4 span { font-weight: 400; font-size: 13px; color: var(--c-primary) }
.meal { display: flex; gap: 12px; align-items: center; padding: 12px 14px; border-radius: var(--r-sm); border: 1px solid var(--c-border-light); margin-bottom: 6px; transition: all .2s }
.meal:hover { border-color: var(--c-primary) }
.mi { font-size: 22px }
.mn { flex: 1; font-size: 14px }
.mn b { font-size: 10px; text-transform: uppercase; letter-spacing: .1em; color: var(--c-primary); margin-right: 8px }
.mn small { display: block; font-size: 12px; color: var(--c-ink-muted); margin-top: 2px }
.ms { font: 700 16px var(--font-display); color: var(--c-primary) }
.btn-log { padding: 4px 10px; border-radius: 4px; background: transparent; border: 1px solid var(--c-border); font-size: 11px; color: var(--c-ink-muted); cursor: pointer; transition: all .15s; white-space: nowrap }
.btn-log:hover { border-color: var(--c-primary); color: var(--c-primary) }
.logged-done { font-size: 11px; color: var(--c-success); white-space: nowrap }
</style>
