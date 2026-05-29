import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useAuth = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const uid = ref(localStorage.getItem('user_id') || '')
  const name = ref(localStorage.getItem('user_name') || '')
  const profile = ref<any>(null)
  const loading = ref(false)
  const err = ref('')
  const isLoggedIn = computed(() => !!token.value)

  function persist() {
    localStorage.setItem('token', token.value)
    localStorage.setItem('user_id', uid.value)
    localStorage.setItem('user_name', name.value)
  }

  async function login(username: string, password: string) {
    loading.value = true; err.value = ''
    try { const r = await api.login(username, password); token.value = r.token; uid.value = r.user_id; name.value = r.name; profile.value = r.profile; persist() }
    catch (e: any) { err.value = e.message; throw e }
    finally { loading.value = false }
  }

  async function register(username: string, password: string, pname: string) {
    loading.value = true; err.value = ''
    try { const r = await api.register(username, password, pname); token.value = r.token; uid.value = r.user_id; name.value = r.name; persist() }
    catch (e: any) { err.value = e.message; throw e }
    finally { loading.value = false }
  }

  async function fetchProfile() {
    try { const r = await api.me(); profile.value = r.profile; name.value = r.profile?.name || name.value }
    catch { /* */ }
  }

  function logout() {
    token.value = ''; uid.value = ''; name.value = ''; profile.value = null
    localStorage.removeItem('token'); localStorage.removeItem('user_id'); localStorage.removeItem('user_name')
  }

  return { token, uid, name, profile, loading, err, isLoggedIn, login, register, fetchProfile, logout }
})
