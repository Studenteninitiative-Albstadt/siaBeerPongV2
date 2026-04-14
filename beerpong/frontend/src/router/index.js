import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import LoginView    from '../views/LoginView.vue'
import AdminView    from '../views/AdminView.vue'
import LiveView     from '../views/LiveView.vue'
import MobileView   from '../views/MobileView.vue'

const routes = [
  { path: '/', redirect: () => {
      const a = useAuthStore()
      if (a.isOrga)     return '/admin'
      if (a.isLiveview) return '/live'
      return '/login'
    },
  },
  { path: '/login',  component: LoginView,  meta: { public: true } },
  { path: '/admin',  component: AdminView,  meta: { requiresOrga: true } },
  { path: '/live',   component: LiveView,   meta: { requiresAuth: true } },
  { path: '/mobile', component: MobileView, meta: { public: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.isAuthenticated) return '/login'
  if (to.meta.requiresOrga && !auth.isOrga) return auth.isLiveview ? '/live' : '/login'
  return true
})

export default router
