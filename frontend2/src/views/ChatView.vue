<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { api } from '@/api'

interface Msg { role: string; content: string }
interface Session { session_id: string; title: string; message_count: number; created_at: string; updated_at: string }

const msgs = ref<Msg[]>([])
const sessions = ref<Session[]>([])
const input = ref('')
const sid = ref('')
const sending = ref(false)
const sidebarOpen = ref(true)
const scrollEl = ref<HTMLElement | null>(null)

function scrollDown() {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
  })
}

function formatTime(s: string) {
  if (!s) return ''; const d = s.slice(0,10); const t = s.slice(11,16)
  return d === new Date().toISOString().slice(0,10) ? t : d
}

async function loadSessionList() {
  try { const r = await api.listSessions(); sessions.value = r.sessions || [] } catch { /* */ }
}

async function loadChat(sessionId: string) {
  sid.value = sessionId; localStorage.setItem('chat_sid', sessionId)
  try {
    const r = await api.getHistory(sessionId, 50)
    msgs.value = r?.history?.length
      ? r.history.map((h: any) => ({ role: h.role, content: h.content }))
      : [{ role: 'assistant', content: '您好！我是您的膳食顾问。您可以询问食材搭配、菜品分析或饮食建议。' }]
  } catch { msgs.value = [{ role: 'assistant', content: '无法加载对话记录。' }] }
  scrollDown()
}

async function newChat() {
  if (sending.value) return
  try {
    const r = await api.createSession()
    sid.value = r.session_id; localStorage.setItem('chat_sid', r.session_id)
    msgs.value = [{ role: 'assistant', content: '您好！我是您的膳食顾问。您可以询问食材搭配、菜品分析或饮食建议。' }]
    await loadSessionList()
  } catch { sid.value = 'local_' + Date.now(); msgs.value = [{ role: 'assistant', content: '您好！(离线模式)' }] }
  scrollDown()
}

async function deleteSession(sessionId: string) {
  try { await api.deleteSession(sessionId) } catch { /* */ }
  sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
  if (sid.value === sessionId) await newChat()
}

onMounted(async () => {
  await loadSessionList()
  const saved = localStorage.getItem('chat_sid')
  if (saved && sessions.value.some(s => s.session_id === saved)) { await loadChat(saved) }
  else if (sessions.value.length > 0) { await loadChat(sessions.value[0].session_id) }
  else { await newChat() }
})

async function send() {
  const t = input.value.trim()
  if (!t || sending.value) return
  input.value = ''
  msgs.value.push({ role: 'user', content: t })
  sending.value = true
  scrollDown()

  try {
    if (!sid.value.startsWith('local_')) { await api.sendChat(sid.value, 'user', t) }

    // 调用 LLM 接口获取 AI 回复（后端会用 Redis 缓存）
    let reply = ''
    try {
      const r = await api.chatAsk(sid.value, t, msgs.value.slice(-6).map(m => ({ role: m.role, content: m.content })))
      reply = r.reply
    } catch {
      // LLM 不可用时降级到本地规则
      reply = fallbackReply(t)
    }

    msgs.value.push({ role: 'assistant', content: reply })
    scrollDown()

    if (!sid.value.startsWith('local_')) {
      await api.sendChat(sid.value, 'assistant', reply)
      await loadSessionList()
    }
  } catch {
    msgs.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用。请确认后端已启动。' })
  }
  sending.value = false; scrollDown()
}

function fallbackReply(t: string): string {
  const extracted = extractIngredients(t)
  if (extracted.length) {
    return `您提到了「${extracted.join('、')}」。如果后端 AI 服务在线，我可以为您做更详细的合规分析。当前 AI 服务暂不可用，请稍后重试。`
  }
  return `您好！我是您的膳食顾问。目前 AI 服务暂不可用（后端 LLM 未连接），请确认后端已正确配置 Moonshot API Key。`
}

function extractIngredients(text: string): string[] {
  const words = text.split(/[,，、\s+]/).map(s=>s.trim()).filter(Boolean)
  const skip = ['吃','喝','做','推荐','什么','怎么','吗','的','了','呢','吧','是','有','能','可以','这个','那个','今天','明天','昨天','我','你','他','给','看','想','要','会','和','与','或','不']
  return words.filter(w => w.length >= 2 && !skip.includes(w))
}
</script>

<template>
  <div class="chat-page">
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-head"><button class="side-new" @click="newChat" :disabled="sending">＋ 新建对话</button></div>
      <div class="side-list">
        <div v-for="s in sessions" :key="s.session_id" :class="['side-item', { active: s.session_id === sid }]" @click="loadChat(s.session_id)">
          <div class="side-title">{{ s.title }}</div>
          <div class="side-meta"><span>{{ s.message_count }} 条</span><span>{{ formatTime(s.updated_at) }}</span><button class="side-del" @click.stop="deleteSession(s.session_id)" title="删除">&times;</button></div>
        </div>
        <div v-if="!sessions.length" class="side-empty">暂无历史对话</div>
      </div>
    </aside>
    <div class="chat-main">
      <div class="chat-head"><button class="toggle-sidebar" @click="sidebarOpen=!sidebarOpen">&equiv;</button><h2 class="pg-title">智能膳食咨询</h2></div>
      <div class="chat-box">
        <div class="chat-scroll" ref="scrollEl">
          <div v-if="sid.startsWith('local_')" class="badge">离线模式</div>
          <div v-for="(m,i) in msgs" :key="i" :class="['msg', m.role]" style="white-space:pre-wrap">{{ m.content }}</div>
          <div v-if="sending" class="msg assistant"><div class="typing"><span></span><span></span><span></span></div></div>
        </div>
        <div class="chat-input">
          <input class="inp" v-model="input" placeholder="输入您的问题..." @keypress.enter="send" :disabled="sending" />
          <button @click="send" :disabled="!input.trim()||sending">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page { display:flex; margin:-32px -24px; min-height:calc(100vh - 56px) }
.sidebar { width:260px; flex-shrink:0; border-right:1px solid var(--c-border-light); background:var(--c-surface); display:flex; flex-direction:column }
.sidebar-head { padding:16px; border-bottom:1px solid var(--c-border-light) }
.side-new { width:100%; padding:10px; border-radius:var(--r-sm); border:1.5px solid var(--c-border); background:transparent; font-size:13px; font-weight:600; color:var(--c-primary); cursor:pointer; transition:all .2s }
.side-new:hover:not(:disabled) { border-color:var(--c-primary); background:var(--c-primary-bg) }
.side-list { flex:1; overflow-y:auto; padding:8px }
.side-item { padding:12px; border-radius:var(--r-sm); cursor:pointer; transition:all .15s; margin-bottom:2px }
.side-item:hover { background:var(--c-bg-alt) }
.side-item.active { background:var(--c-primary-bg) }
.side-title { font-size:13px; font-weight:500; color:var(--c-ink); overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
.side-meta { display:flex; align-items:center; gap:8px; margin-top:4px; font-size:11px; color:var(--c-ink-muted) }
.side-del { margin-left:auto; background:none; color:var(--c-ink-muted); font-size:16px; padding:0 4px; opacity:0; transition:opacity .15s }
.side-item:hover .side-del { opacity:1 }
.side-del:hover { color:var(--c-danger) }
.side-empty { padding:32px; text-align:center; font-size:13px; color:var(--c-ink-muted) }
.chat-main { flex:1; display:flex; flex-direction:column; padding:24px; min-width:0 }
.chat-head { display:flex; align-items:center; gap:12px; margin-bottom:20px }
.pg-title { font:700 26px var(--font-display); margin:0 }
.toggle-sidebar { display:none; background:none; font-size:20px; color:var(--c-ink-soft); padding:4px }
.chat-box { background:var(--c-surface); border:1px solid var(--c-border-light); border-radius:var(--r); overflow:hidden; display:flex; flex-direction:column; flex:1 }
.chat-scroll { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:10px; min-height:300px }
.badge { font-size:11px; color:var(--c-accent); text-align:center; padding:4px 10px; background:var(--c-accent-bg); border-radius:6px; align-self:center }
.msg { max-width:80%; padding:12px 18px; border-radius:14px; font-size:14px; line-height:1.7; animation:mi .25s ease }
@keyframes mi { from{ opacity:0; transform:translateY(6px) } to{ opacity:1; transform:translateY(0) } }
.msg.user { align-self:flex-end; background:var(--c-primary); color:white; border-bottom-right-radius:4px }
.msg.assistant { align-self:flex-start; background:var(--c-bg); border:1px solid var(--c-border-light); border-bottom-left-radius:4px; color:var(--c-ink-soft) }
.typing { display:flex; gap:4px; align-items:center; padding:4px 0 }
.typing span { width:8px; height:8px; border-radius:50%; background:var(--c-ink-muted); animation:dotBounce 1.4s ease-in-out infinite }
.typing span:nth-child(2){ animation-delay:.2s }
.typing span:nth-child(3){ animation-delay:.4s }
@keyframes dotBounce{ 0%,60%,100%{ transform:translateY(0); opacity:.4 } 30%{ transform:translateY(-4px); opacity:1 } }
.chat-input { display:flex; gap:8px; padding:14px; border-top:1px solid var(--c-border-light); background:var(--c-bg) }
.chat-input input { border-radius:24px; flex:1; padding:12px 18px }
.chat-input input::placeholder { color:var(--c-ink-muted) }
.chat-input button { padding:10px 24px; border-radius:24px; background:var(--c-primary); color:white; font-size:14px; font-weight:600; transition:all .2s }
.chat-input button:hover:not(:disabled) { background:var(--c-primary-light) }
.chat-input button:disabled { opacity:.5; cursor:not-allowed }
@media(max-width:900px){ .sidebar{ display:none } .sidebar.open{ display:flex; position:fixed; inset:0; z-index:200; width:280px } .toggle-sidebar{ display:block } }
</style>
