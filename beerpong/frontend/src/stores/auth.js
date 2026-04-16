import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api.js'

export const useAuthStore = defineStore('auth', () => {
  const accessToken  = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))

  function _decode(token) {
    try { return JSON.parse(atob(token.split('.')[1])) } catch { return null }
  }

  const payload      = computed(() => accessToken.value ? _decode(accessToken.value) : null)
  const isAuthenticated = computed(() => !!accessToken.value)
  const isOrga       = computed(() => !!payload.value?.is_orga)
  const isLiveview   = computed(() => !!payload.value?.is_liveview)
  const isRoot       = computed(() => !!payload.value?.is_root)
  const username     = computed(() => payload.value?.username ?? null)

  async function login(user, pass) {
    const data = await api.auth.login(user, pass)
    if (!data.access) throw new Error('No token received')
    accessToken.value  = data.access
    refreshToken.value = data.refresh
    localStorage.setItem('access_token',  data.access)
    localStorage.setItem('refresh_token', data.refresh)
    return data
  }

  function logout() {
    accessToken.value  = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { accessToken, refreshToken, isAuthenticated, isOrga, isLiveview, isRoot, username, login, logout }
})
