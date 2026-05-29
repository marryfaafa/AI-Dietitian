<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'

const report = ref('')
const meals = ref<any[]>([])
const checkName = ref('')
const checkIngs = ref('')
const checkResult = ref<any>(null)
const logName = ref('')
const logType = ref('午餐')
const logRating = ref(3)
const logMsg = ref('')

onMounted(async () => {
  try { const r = await api.getReport(); report.value = r.report; meals.value = r.recent_meals || [] } catch { /* */ }
})

async function quickCheck() {
  const ings = checkIngs.value.split(/[,，]/).map(s=>s.trim()).filter(Boolean)
  if (!checkName.value || !ings.length) return
  try { checkResult.value = await api.checkCompliance({ recipe_name: checkName.value, ingredients: ings }) }
  catch (e: any) { checkResult.value = { error: e.message } }
}

async function logMeal() {
  if (!logName.value.trim()) return
  logMsg.value = ''
  try {
    await api.logMeal({ recipe_name: logName.value, meal_type: logType.value, rating: logRating.value })
    logMsg.value = `已记录「${logName.value}」`
    logName.value = ''
    // 刷新用餐记录
    const r = await api.getReport()
    meals.value = r.recent_meals || []
  } catch (e: any) { logMsg.value = '记录失败: ' + e.message }
}
</script>

<template>
  <div>
    <h2 class="pg-title">合规报告</h2>
    <div class="grid2">
      <div class="box">
        <h3>饮食健康分析</h3>
        <pre class="txt" v-if="report">{{ report }}</pre>
        <p v-else class="muted">请先完善健康画像</p>
      </div>
      <div class="box">
        <h3>食谱快速检查</h3>
        <input v-model="checkName" class="inp" placeholder="菜谱名称" />
        <input v-model="checkIngs" class="inp" placeholder="食材，逗号分隔" style="margin-top:8px" />
        <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" @click="quickCheck">合规检查</button>
        <div v-if="checkResult" class="chk-result" :class="{pass:checkResult.is_compliant}">
          <div v-if="checkResult.error" style="color:var(--c-danger)">{{ checkResult.error }}</div>
          <template v-else>
            <strong>{{ checkResult.is_compliant ? '适宜' : '不适宜' }}</strong> 评分 {{ checkResult.score?.toFixed(1) }}
            <div v-if="checkResult.warnings?.length" style="color:var(--c-danger);font-size:12px;margin-top:4px">{{ checkResult.warnings.join('; ') }}</div>
          </template>
        </div>
      </div>
    </div>

    <div class="grid2" style="margin-top:20px">
      <div class="box">
        <h3>近7天用餐 <small style="font-weight:400;font-size:12px;color:var(--c-ink-muted)">共 {{ meals.length }} 条</small></h3>
        <div v-if="!meals.length" class="muted">暂无记录 — 在右侧记录你的用餐</div>
        <div v-for="m in meals" :key="m.created_at" class="meal-row">{{ m.recipe_name }} · {{ m.meal_type }} · {{ m.created_at?.slice(0,10) }}</div>
      </div>
      <div class="box">
        <h3>记录用餐</h3>
        <label style="font-size:13px;color:var(--c-ink-soft);display:block;margin-bottom:4px">菜名</label>
        <input v-model="logName" class="inp" placeholder="如：清蒸鲈鱼" />
        <label style="font-size:13px;color:var(--c-ink-soft);display:block;margin:10px 0 4px">餐类</label>
        <select v-model="logType" class="inp" style="cursor:pointer">
          <option>早餐</option><option>午餐</option><option>晚餐</option><option>加餐</option>
        </select>
        <label style="font-size:13px;color:var(--c-ink-soft);display:block;margin:10px 0 4px">评价</label>
        <div style="display:flex;gap:4px;margin-bottom:10px">
          <span v-for="s in 5" :key="s" class="star" :class="{on: s <= logRating}" @click="logRating = s">{{ s <= logRating ? '★' : '☆' }}</span>
        </div>
        <button class="btn btn-primary" style="width:100%;justify-content:center" @click="logMeal">记录用餐</button>
        <p v-if="logMsg" style="font-size:13px;color:var(--c-success);margin-top:8px">{{ logMsg }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pg-title { font: 700 26px var(--font-display); margin-bottom: 8px }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px }
.box { background: var(--c-surface); border: 1px solid var(--c-border-light); border-radius: var(--r); padding: 24px }
.box h3 { font: 600 15px var(--font-display); padding-bottom: 12px; margin-bottom: 16px; border-bottom: 2px solid var(--c-border-light) }
.txt { white-space: pre-wrap; font-size: 13px; line-height: 1.8; color: var(--c-ink-soft) }
.chk-result { margin-top: 10px; padding: 12px; border-radius: var(--r-sm); font-size: 13px; background: var(--c-danger-bg); border: 1px solid rgba(192,72,72,.15) }
.chk-result.pass { background: var(--c-primary-bg); border-color: rgba(61,94,58,.15) }
.meal-row { padding: 8px 0; border-bottom: 1px solid var(--c-border-light); font-size: 14px; color: var(--c-ink-soft) }
.meal-row:last-child { border: none }
.muted { color: var(--c-ink-muted); font-size: 14px }
.star { font-size: 22px; cursor: pointer; color: var(--c-border); transition: color .15s; user-select: none }
.star.on { color: #E0A840 }
.star:hover { color: #D49530 }
@media(max-width:768px){ .grid2{ grid-template-columns:1fr } }
</style>
