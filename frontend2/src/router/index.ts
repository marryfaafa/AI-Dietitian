import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomeView.vue'), meta: { guest: true } },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/DashboardView.vue'), meta: { auth: true } },
  { path: '/profile', name: 'Profile', component: () => import('@/views/ProfileView.vue'), meta: { auth: true } },
  { path: '/report', name: 'Report', component: () => import('@/views/ReportView.vue'), meta: { auth: true } },
  { path: '/meals', name: 'Meals', component: () => import('@/views/MealPlanView.vue'), meta: { auth: true } },
  { path: '/chat', name: 'Chat', component: () => import('@/views/ChatView.vue'), meta: { auth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  const a = useAuth()
  if (to.meta.auth && !a.token) return next('/login')
  if (to.meta.guest && a.token && to.name !== 'Home') return next('/dashboard')
  next()
})

export default router
