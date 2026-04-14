import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, createWebSocket } from '../api.js'
import { useAuthStore } from './auth.js'

export const useTournamentStore = defineStore('tournament', () => {
  const tournament     = ref(null)
  const teams          = ref([])
  const teamPlayers    = ref({})
  const groupPhase     = ref({})
  const groupStandings = ref({})
  const playin         = ref({})
  const koPhase        = ref({ rounds: [] })
  const tournaments    = ref([])
  const ws             = ref(null)
  const wsConnected    = ref(false)

  function _apply(data) {
    if (data.tournament)      tournament.value     = data.tournament
    if (data.teams)           teams.value          = data.teams
    if (data.team_players)    teamPlayers.value    = data.team_players
    if (data.group_phase)     groupPhase.value     = data.group_phase
    if (data.group_standings) groupStandings.value = data.group_standings
    if (data.playin)          playin.value         = data.playin
    if (data.ko_phase)        koPhase.value        = data.ko_phase
  }

  async function fetchList() {
    const data = await api.tournaments.list()
    tournaments.value = Array.isArray(data) ? data : (data.results ?? [])
  }

  async function load(id) {
    _apply(await api.tournaments.loadAllData(id))
  }

  async function create(data) {
    const result = await api.tournaments.create(data)
    tournament.value = result
    teams.value = []
    groupPhase.value = {}
    groupStandings.value = {}
    playin.value = {}
    koPhase.value = { rounds: [] }
    return result
  }

  async function remove(id) {
    await api.tournaments.delete(id)
    if (tournament.value?.id === id) tournament.value = null
    tournaments.value = tournaments.value.filter(t => t.id !== id)
  }

  function connect(tournamentId) {
    const auth = useAuthStore()
    _disconnect()
    const socket = createWebSocket(tournamentId, auth.accessToken, null)
    ws.value = socket
    socket.onopen    = () => { wsConnected.value = true }
    socket.onmessage = (e) => { try { const m = JSON.parse(e.data); if (m.data) _apply(m.data) } catch {} }
    socket.onclose   = () => { wsConnected.value = false; ws.value = null }
    socket.onerror   = (e) => console.error('WS error', e)
  }

  function connectMobile(tournamentId, mobileToken) {
    _disconnect()
    const socket = createWebSocket(tournamentId, null, mobileToken)
    ws.value = socket
    socket.onopen    = () => { wsConnected.value = true }
    socket.onmessage = (e) => { try { const m = JSON.parse(e.data); if (m.data) _apply(m.data) } catch {} }
    socket.onclose   = () => { wsConnected.value = false; ws.value = null }
  }

  function _disconnect() {
    if (ws.value) { ws.value.close(); ws.value = null }
    wsConnected.value = false
  }

  return {
    tournament, teams, groupPhase, groupStandings, playin, koPhase,
    tournaments, ws, wsConnected,
    fetchList, load, create, remove, connect, connectMobile,
    disconnect: _disconnect,
  }
})
