import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import LoginView    from '../views/LoginView.vue'
import AdminView    from '../views/AdminView.vue'
import LiveView     from '../views/LiveView.vue'
import MobileView   from '../views/MobileView.vue'
import RefereeView  from '../views/RefereeView.vue'

const routes = [
  { path: '/', redirect: () => {
      const a = useAuthStore()
      if (a.isRoot)     return '/admin'     // root → full admin
      if (a.isOrga)     return '/referee'   // regular orga → referee waiting screen
      if (a.isLiveview) return '/live'
      return '/login'
    },
  },
  { path: '/login',   component: LoginView,   meta: { public: true } },
  { path: '/admin',   component: AdminView,   meta: { requiresRoot: true } },
  { path: '/referee', component: RefereeView, meta: { requiresOrga: true } },
  { path: '/live',    component: LiveView,    meta: { requiresAuth: true } },
  { path: '/mobile',  component: MobileView,  meta: { public: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.isAuthenticated) return '/login'
  if (to.meta.requiresRoot && !auth.isRoot) {
    // root route: only root/staff may enter; regular referees go to /referee
    return auth.isOrga ? '/referee' : auth.isLiveview ? '/live' : '/login'
  }
  if (to.meta.requiresOrga && !auth.isOrga) return auth.isLiveview ? '/live' : '/login'
  return true
})

export default router
