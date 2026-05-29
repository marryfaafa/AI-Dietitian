const B = '/api'

function hd(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  const t = localStorage.getItem('token')
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

async function req<T>(m: string, u: string, b?: any): Promise<T> {
  const o: RequestInit = { method: m, headers: hd() }
  if (b) o.body = JSON.stringify(b)
  const r = await fetch(B + u, o)
  const d = await r.json()
  if (!d.success) throw new Error(d.error || '请求失败')
  return d as T
}

export const api = {
  register: (username: string, password: string, name: string) =>
    req<{ token: string; user_id: string; name: string }>('POST', '/auth/register', { username, password, name }),
  login: (username: string, password: string) =>
    req<{ token: string; user_id: string; name: string; profile: any }>('POST', '/auth/login', { username, password }),
  me: () => req<{ user_id: string; profile: any }>('GET', '/auth/me'),
  healthOpts: () => req<{ constitutions: any[]; conditions: any[]; restrictions: any[] }>('GET', '/health/options'),
  getProfile: () => req<{ profile: any }>('GET', '/user/profile'),
  updateProfile: (d: any) => req<any>('PUT', '/user/profile', d),
  getReport: () => req<{ report: string; stats: any; recent_meals: any[] }>('GET', '/user/report'),
  logMeal: (d: any) => req<{ log_id: number }>('POST', '/user/meal', d),
  checkCompliance: (d: any) => req<any>('POST', '/compliance/check', d),
  planDaily: (d: any) => req<any>('POST', '/meal/plan/daily', d),
  planWeekly: (d: any) => req<any>('POST', '/meal/plan/weekly', d),
  createSession: (d?: any) => req<{ session_id: string }>('POST', '/session/create', d || {}),
  sendChat: (sid: string, role: string, content: string) =>
    req<{ history: any[] }>('POST', `/session/${sid}/chat`, { role, content }),
  getHistory: (sid: string, n = 10) =>
    req<{ history: any[] }>('GET', `/session/${sid}/history?n=${n}`),
  listSessions: () => req<{ sessions: any[] }>('GET', '/session/list'),
  deleteSession: (sid: string) => req<any>('DELETE', `/session/${sid}`),
  chatAsk: (sid: string, question: string, history: any[]) =>
    req<{ reply: string }>('POST', '/chat/ask', { session_id: sid, question, history }),
  health: () => req<{ status: string }>('GET', '/health'),
}
