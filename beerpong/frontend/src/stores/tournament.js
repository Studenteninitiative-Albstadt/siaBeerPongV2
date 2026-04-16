import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, createWebSocket } from '../api.js'
import { useAuthStore } from './auth.js'

export const useTournamentStore = defineStore('tournament', () => {
  const tournament     = ref(null)
  const teams          = ref([])
  const teamPlayers    = ref({})
  const topPlayers     = ref([])
  const groupPhase     = ref({})
  const groupStandings = ref({})
  const playin         = ref({})
  const koPreview      = ref({})
  const koPhase        = ref({ rounds: [] })
  const tournaments    = ref([])
  const ws             = ref(null)
  const wsConnected    = ref(false)

  function _apply(data) {
    if (data.tournament)      tournament.value     = data.tournament
    else if (data.id && data.name) tournament.value = data // Fallback: data IS the tournament

    if ('teams' in data)           teams.value          = data.teams || []
    if ('team_players' in data)    teamPlayers.value    = data.team_players || {}
    if ('top_players' in data)     topPlayers.value     = data.top_players || []
    if ('group_phase' in data)     groupPhase.value     = data.group_phase || {}
    if ('group_standings' in data) groupStandings.value = data.group_standings || {}
    if ('playin' in data)          playin.value         = data.playin || {}
    if ('ko_preview' in data)      koPreview.value      = data.ko_preview || {}
    if ('ko_phase' in data)        koPhase.value        = data.ko_phase || { rounds: [] }

    if (data.match) {
      const m = data.match
      const gname = m.group_name
      if (groupPhase.value?.matches?.[gname]) {
        const idx = groupPhase.value.matches[gname].findIndex(x => x.id === m.id)
        if (idx !== -1) {
          groupPhase.value.matches[gname][idx] = { ...groupPhase.value.matches[gname][idx], ...m }
        }
      }
    }

    // Single KO match update (from ko_match_updated broadcast)
    if (data.id !== undefined && !data.tournament && !data.ko_phase && !data.group_phase && data.cups_team1 !== undefined) {
      for (const round of (koPhase.value.rounds || [])) {
        let idx = (round.matches || []).findIndex(m => m.id === data.id)
        if (
          idx === -1 &&
          round?.round_name === data.ko_round &&
          (round?.bracket_type || 'main') === (data.ko_bracket_type || 'main')
        ) {
          idx = (round.matches || []).findIndex(m =>
            Number(m?.ko_match_index ?? -1) === Number(data.ko_match_index ?? -1)
          )
        }
        if (idx !== -1) {
          round.matches[idx] = { ...round.matches[idx], ...data }
          break
        }
      }
    }
  }

  async function fetchList() {
    const data = await api.tournaments.list()
    tournaments.value = Array.isArray(data) ? data : (data.results ?? [])
  }

  async function load(id) {
    _apply(await api.tournaments.loadAllData(id))
  }

  function applyState(data) {
    _apply(data || {})
  }

  async function create(data) {
    const result = await api.tournaments.create(data)
    tournament.value = result
    teams.value = []
    groupPhase.value = {}
    groupStandings.value = {}
    playin.value = {}
    koPreview.value = {}
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
    tournament, teams, teamPlayers, topPlayers, groupPhase, groupStandings, playin, koPreview, koPhase,
    tournaments, ws, wsConnected,
    fetchList, load, create, remove, connect, connectMobile, applyState,
    disconnect: _disconnect,
  }
})
