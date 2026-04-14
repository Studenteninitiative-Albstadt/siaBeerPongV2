/**
 * Centralized API client used by AdminView, LiveView and MobileView.
 * Existing sub-components (GroupsView, KnockoutView, …) use raw fetch(),
 * which is intercepted by fetch.js for JWT injection.
 */

export const API_BASE = import.meta.env.VITE_API_BASE || ''

function getToken() {
  return localStorage.getItem('access_token')
}

async function tryRefresh() {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) throw new Error('no refresh token')
  const res = await fetch(`${API_BASE}/auth/token/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) throw new Error('refresh failed')
  const data = await res.json()
  localStorage.setItem('access_token', data.access)
  if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
  return data.access
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    try {
      const newToken = await tryRefresh()
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(`${API_BASE}${path}`, { ...options, headers })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.hash = '/login'
      throw new Error('Authentication failed')
    }
  }

  return res.json()
}

const get  = (p)    => request(p)
const post = (p, b) => request(p, { method: 'POST',   body: JSON.stringify(b) })
const del  = (p)    => request(p, { method: 'DELETE' })

export const api = {
  auth: {
    login: (username, password) =>
      request('/auth/token', { method: 'POST', body: JSON.stringify({ username, password }) }),
  },

  tournaments: {
    list:           ()        => get('/tournaments'),
    create:         (d)       => post('/tournaments', d),
    get:            (id)      => get(`/tournaments/${id}`),
    update:         (id, d)   => post(`/tournaments/${id}/update`, d),
    delete:         (id)      => del(`/tournaments/${id}`),
    computePlan:    (id, d)   => post(`/tournaments/${id}/compute-plan`, d),
    saveTeams:      (id, ts)  => post(`/tournaments/${id}/save-teams`, { teams: ts }),
    loadTeams:      (id)      => get(`/tournaments/${id}/load-teams`),
    generateGroups: (id, ts)  => post(`/tournaments/${id}/generate-groups`, { teams: ts }),
    saveGroupPhase: (id, d)   => post(`/tournaments/${id}/save-group-phase`, d),
    groupMatch:     (id, d)   => post(`/tournaments/${id}/group-match`, d),
    groupStandings: (id)      => get(`/tournaments/${id}/group-standings`),
    loadAllData:    (id)      => get(`/tournaments/${id}/load-all-data`),
    savePlayin:     (id, d)   => post(`/tournaments/${id}/save-playin`, d),
    loadPlayin:     (id)      => get(`/tournaments/${id}/load-playin`),
    saveKoPreview:  (id, d)   => post(`/tournaments/${id}/save-ko-preview`, d),
    saveKoBracket:  (id, d)   => post(`/tournaments/${id}/save-ko-bracket`, d),
    loadKoBracket:  (id)      => get(`/tournaments/${id}/load-ko-bracket`),
    koMatch:        (id, d)   => post(`/tournaments/${id}/ko-match`, d),
    mobileState:    (id, tok) => get(`/tournaments/${id}/mobile-state?token=${tok}`),
  },
}

export function createWebSocket(tournamentId, jwtToken, mobileToken) {
  const wsBase = (API_BASE || window.location.origin).replace(/^http/, 'ws')
  const param = jwtToken
    ? `?token=${jwtToken}`
    : mobileToken
      ? `?mobile_token=${mobileToken}`
      : ''
  return new WebSocket(`${wsBase}/ws/tournament/${tournamentId}/${param}`)
}
