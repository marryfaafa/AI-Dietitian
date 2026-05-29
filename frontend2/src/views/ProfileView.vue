<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAuth } from '@/stores/auth'

const auth = useAuth()
const loading = ref(true)
const err = ref('')
const constitutions = ref<any[]>([])
const conditions = ref<any[]>([])
const restrictions = ref<any[]>([])
const sc = ref<string[]>([])
const sco = ref<string[]>([])
const sr = ref<string[]>([])
const msg = ref('')
const saving = ref(false)

// 离线后备数据
const fallback = {
  con: [
    {name:'平和质',description:'阴阳气血调和'},
    {name:'气虚质',description:'元气不足'},
    {name:'阳虚质',description:'畏寒怕冷'},
    {name:'阴虚质',description:'口干舌燥'},
    {name:'痰湿质',description:'形体肥胖'},
    {name:'湿热质',description:'面垢油光'},
    {name:'血瘀质',description:'肤色晦暗'},
    {name:'气郁质',description:'神情抑郁'},
    {name:'特禀质',description:'过敏体质'},
  ],
  cond: [
    {name:'糖尿病',description:'血糖代谢异常'},
    {name:'高血压',description:'血压持续升高'},
    {name:'高血脂',description:'血脂水平异常'},
    {name:'高尿酸/痛风',description:'嘌呤代谢紊乱'},
    {name:'胃炎/胃溃疡',description:'胃粘膜炎症'},
    {name:'肾病',description:'肾脏功能减退'},
  ],
  res: [
    {name:'海鲜过敏'},{name:'花生过敏'},{name:'牛奶不耐受/乳糖不耐'},
    {name:'鸡蛋过敏'},{name:'大豆过敏'},{name:'坚果过敏'},
    {name:'素食'},{name:'清真饮食'},{name:'术后恢复'},{name:'孕妇'},
  ],
}

onMounted(async () => {
  try {
    const o = await api.healthOpts()
    constitutions.value = o.constitutions
    conditions.value = o.conditions
    restrictions.value = o.restrictions
  } catch (e) {
    err.value = '服务暂不可用，使用离线数据'
    // fallback to inline data
    constitutions.value = fallback.con
    conditions.value = fallback.cond
    restrictions.value = fallback.res
  }
  // 加载已有画像
  try {
    const p = await api.getProfile()
    if (p?.profile) {
      sc.value = Array.isArray(p.profile.constitutions) ? p.profile.constitutions : []
      sco.value = Array.isArray(p.profile.health_conditions) ? p.profile.health_conditions : []
      sr.value = Array.isArray(p.profile.dietary_restrictions) ? p.profile.dietary_restrictions : []
    }
  } catch { /* 新用户无需画像 */ }
  loading.value = false
})

function tg(arr: string[], v: string) { const i = arr.indexOf(v); i > -1 ? arr.splice(i,1) : arr.push(v) }

async function save() {
  saving.value = true; msg.value = ''
  try {
    await api.updateProfile({ constitutions: sc.value, conditions: sco.value, restrictions: sr.value })
    await auth.fetchProfile()
    msg.value = '保存成功'
    setTimeout(() => msg.value = '', 2000)
  } catch (e: any) { msg.value = e.message }
  saving.value = false
}
</script>

<template>
  <div>
    <h2 class="pg-title">健康画像</h2>
    <p class="pg-sub">完善以下信息，获取更精准的膳食建议</p>

    <div v-if="loading" style="display:flex;align-items:center;gap:10px;padding:40px;color:var(--c-ink-muted)">
      <div class="spinner"></div>加载中...
    </div>

    <div v-if="err" style="font-size:12px;color:var(--c-accent);margin-bottom:12px;padding:8px 14px;background:var(--c-accent-bg);border-radius:var(--r-sm)">
      {{ err }}
    </div>

    <template v-if="!loading">
      <div class="grid2">
        <div class="box">
          <h3>体质辨识 <small>(可多选)</small></h3>
          <div class="chips">
            <span v-for="c in constitutions" :key="c.name" :class="{sel:sc.includes(c.name)}" @click="tg(sc,c.name)" :title="c.description">{{ c.name }}</span>
          </div>
        </div>
        <div class="box">
          <h3>健康关注 <small>(可多选)</small></h3>
          <div class="chips">
            <span v-for="c in conditions" :key="c.name" :class="{sel:sco.includes(c.name)}" @click="tg(sco,c.name)" :title="c.description">{{ c.name }}</span>
          </div>
        </div>
      </div>
      <div class="box" style="margin-top:20px">
        <h3>饮食限制 <small>(可多选)</small></h3>
        <div class="chips">
          <span v-for="r in restrictions" :key="r.name" :class="{sel:sr.includes(r.name),danger:true}" @click="tg(sr,r.name)">{{ r.name }}</span>
        </div>
      </div>
      <div class="save-bar">
        <button class="btn btn-primary" :disabled="saving" @click="save">{{ saving ? '保存中...' : '保存画像' }}</button>
        <span v-if="msg" :style="{color:msg.includes('成功')?'var(--c-success)':'var(--c-danger)'}">{{ msg }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pg-title { font: 700 26px var(--font-display) }
.pg-sub { font-size: 14px; color: var(--c-ink-muted); margin-bottom: 20px }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px }
.box { background: var(--c-surface); border: 1px solid var(--c-border-light); border-radius: var(--r); padding: 24px }
.box h3 { font: 600 15px var(--font-display); margin-bottom: 14px; display: flex; align-items: baseline; gap: 6px }
.box h3 small { font-size: 12px; color: var(--c-ink-muted); font-weight: 400 }
.chips { display: flex; flex-wrap: wrap; gap: 8px }
.chips span { padding: 7px 14px; border-radius: 20px; border: 1.5px solid var(--c-border); font-size: 13px; cursor: pointer; transition: all .2s; user-select: none; color: var(--c-ink-soft); background: var(--c-bg) }
.chips span:hover { border-color: var(--c-primary); color: var(--c-primary) }
.chips span.sel { background: var(--c-primary); border-color: var(--c-primary); color: white; font-weight: 500 }
.chips span.danger { border-color: #e8c8c8 }
.chips span.danger.sel { background: var(--c-danger); border-color: var(--c-danger); color: white }
.save-bar { display: flex; align-items: center; gap: 16px; margin-top: 24px }
@media(max-width:768px){ .grid2{ grid-template-columns:1fr } }
</style>
