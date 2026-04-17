<template>
  <div class="min-vh-100 bg-dark text-light d-flex flex-column"
       style="background:radial-gradient(circle at top,#1a1a2e 0%,#0d0d0d 55%,#000 100%)">

    <!-- Header -->
    <div class="bg-black border-bottom border-secondary px-4 py-3 d-flex justify-content-between align-items-center">
      <div class="d-flex align-items-center gap-3">
        <img src="/weiß.png" alt="SIA Logo" class="referee-logo" />
        <span class="fw-bold">SIA Bier Pong · Schiedsrichter</span>
      </div>
      <div class="d-flex align-items-center gap-3">
        <span :class="wsConnected ? 'text-success' : 'text-secondary'" class="small">
          {{ wsConnected ? '● Verbunden' : '○ Getrennt' }}
        </span>
        <span class="text-secondary small">{{ auth.username }}</span>
        <button class="btn btn-sm btn-outline-secondary" @click="handleLogout">Abmelden</button>
      </div>
    </div>

    <!-- Tournament picker -->
    <div v-if="!tournamentId" class="flex-grow-1 d-flex align-items-center justify-content-center p-4">
      <div class="card bg-black border-secondary text-light" style="max-width:480px; width:100%">
        <div class="card-header bg-black border-secondary fw-bold">Turnier auswählen</div>
        <div class="card-body">
          <div v-if="loadingTournaments" class="text-secondary text-center py-3">
            <div class="spinner-border spinner-border-sm me-2"></div>Lade Turniere…
          </div>
          <div v-else-if="tournaments.length === 0" class="text-secondary text-center py-3">
            Keine aktiven Turniere verfügbar.
          </div>
          <div v-else class="list-group">
            <button v-for="t in tournaments" :key="t.id"
                    class="list-group-item list-group-item-action bg-dark text-light border-secondary"
                    @click="selectTournament(t.id)">
              <div class="fw-bold">{{ t.name }}</div>
              <div class="small text-secondary">Phase: {{ t.current_phase ?? t.currentPhase ?? '—' }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main area -->
    <div v-else class="flex-grow-1 d-flex flex-column">

      <!-- Waiting screen -->
      <div v-if="!assignment" class="flex-grow-1 d-flex flex-column align-items-center justify-content-center p-4 text-center">
        <div class="waiting-pulse mb-4">
          <div class="waiting-circle"></div>
        </div>
        <h4 class="mb-2">Warten auf Spielzuweisung</h4>
        <p class="text-secondary small mb-4">Der Root-Admin weist dir gleich ein Spiel zu.</p>
        <div class="small text-secondary">Turnier: <strong class="text-light">{{ tournamentName }}</strong></div>
      </div>

      <!-- Assigned match -->
      <div v-else class="flex-grow-1 d-flex flex-column p-3 gap-3" style="overflow-y:auto">

        <!-- Match header -->
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div class="d-flex align-items-center gap-2">
            <span class="badge bg-primary">
              {{ assignment.phase === 'ko' ? 'KO' : 'Gruppe ' + (assignment.group_name ?? '') }}
            </span>
            <span v-if="assignment.table_no" class="text-secondary small">{{ assignment.table_no }}</span>
          </div>
          <div v-if="matchState?.is_overtime" class="badge bg-warning text-dark">Verlängerung</div>
          <div v-if="matchState?.winner" class="badge bg-success fs-6">Spiel beendet</div>
        </div>

        <!-- ── Schützenauswahl Overlay ── -->
        <div v-if="pendingShooter"
             class="p-4 border border-warning rounded bg-dark text-center shadow-lg">
          <h5 class="text-warning mb-3">
            {{ pendingShooter.mode === 'overtime_credit'
               ? `Nachwurf für ${pendingShooter.teamName}!`
               : `Treffer für ${pendingShooter.teamName}!` }}
          </h5>

          <!-- Overtime credit allocation -->
          <template v-if="pendingShooter.mode === 'overtime_credit'">
            <p class="text-light mb-2">Verteile die {{ pendingShooter.bonusCupCount }} Nachwurf-Becher.</p>
            <div class="text-secondary small mb-3">Noch zu verteilen: {{ overtimeRemainingCups }}</div>
            <div class="d-flex justify-content-center gap-3 flex-wrap mb-3">
              <div v-if="pendingShooter.p1">
                <div class="text-light fw-semibold mb-1">{{ pendingShooter.p1 }}</div>
                <div class="btn-group">
                  <button class="btn btn-outline-secondary btn-sm" @click="adjustOvertimeAlloc('p1',-1)"
                          :disabled="(pendingShooter.bonusP1||0)<=0">−</button>
                  <span class="btn btn-outline-light btn-sm disabled">{{ pendingShooter.bonusP1||0 }}</span>
                  <button class="btn btn-outline-warning btn-sm" @click="adjustOvertimeAlloc('p1',1)"
                          :disabled="overtimeRemainingCups<=0">+</button>
                </div>
              </div>
              <div v-if="pendingShooter.p2">
                <div class="text-light fw-semibold mb-1">{{ pendingShooter.p2 }}</div>
                <div class="btn-group">
                  <button class="btn btn-outline-secondary btn-sm" @click="adjustOvertimeAlloc('p2',-1)"
                          :disabled="(pendingShooter.bonusP2||0)<=0">−</button>
                  <span class="btn btn-outline-light btn-sm disabled">{{ pendingShooter.bonusP2||0 }}</span>
                  <button class="btn btn-outline-warning btn-sm" @click="adjustOvertimeAlloc('p2',1)"
                          :disabled="overtimeRemainingCups<=0">+</button>
                </div>
              </div>
            </div>
          </template>

          <!-- Normal player selection -->
          <template v-else>
            <p class="text-light mb-3">Wer hat den Becher getroffen?</p>
            <div class="d-flex justify-content-center gap-3 mb-3">
              <button v-if="pendingShooter.p1"
                      class="btn btn-lg px-4 py-3 fw-bold"
                      :class="selectedPlayer === pendingShooter.p1 ? 'btn-success' : 'btn-outline-success'"
                      @click="selectedPlayer = pendingShooter.p1">
                {{ pendingShooter.p1 }}
              </button>
              <button v-if="pendingShooter.p2"
                      class="btn btn-lg px-4 py-3 fw-bold"
                      :class="selectedPlayer === pendingShooter.p2 ? 'btn-success' : 'btn-outline-success'"
                      @click="selectedPlayer = pendingShooter.p2">
                {{ pendingShooter.p2 }}
              </button>
            </div>
          </template>

          <div class="d-flex justify-content-center gap-2">
            <button class="btn btn-outline-secondary" @click="cancelShooter">
              {{ pendingShooter.mode === 'overtime_credit' ? 'Zurück' : 'Abbruch (Undo)' }}
            </button>
            <button class="btn btn-primary btn-lg px-5 fw-bold"
                    :disabled="pendingShooter.mode === 'overtime_credit' ? !isOvertimeAllocationComplete : !selectedPlayer"
                    @click="confirmShooter">
              {{ pendingShooter.mode === 'overtime_credit' ? 'Nachwurf Bestätigen' : 'Treffer Bestätigen' }}
            </button>
          </div>
        </div>

        <!-- ── Abschluss-Dialog Overlay ── -->
        <div v-else-if="pendingConclusion"
             class="p-4 border border-primary rounded bg-dark text-center shadow-lg">
          <h5 class="text-primary mb-3">Spielabschluss</h5>

          <template v-if="pendingConclusion.step === 'NACHWURF'">
            <p class="text-light mb-4 fs-5">Alle Becher getroffen! Gibt es einen <strong>Nachwurf</strong>?</p>
            <div class="d-flex justify-content-center gap-3">
              <button class="btn btn-lg btn-primary px-4 fw-bold" @click="conclusionStep('ALL_HIT')">Ja (Nachwurf)</button>
              <button class="btn btn-lg btn-outline-primary px-4 fw-bold" @click="conclusionStep('END_QUERY')">Nein (Direkter Sieg)</button>
            </div>
          </template>

          <template v-else-if="pendingConclusion.step === 'ALL_HIT'">
            <p class="text-light mb-4 fs-5">Wurden beim Nachwurf <strong>alle verbleibenden Becher</strong> getroffen?</p>
            <div class="d-flex justify-content-center gap-3">
              <button class="btn btn-lg btn-warning px-4 fw-bold" @click="conclusionOvertime">Ja (Verlängerung 3 Becher)</button>
              <button class="btn btn-lg btn-outline-primary px-4 fw-bold" @click="conclusionStep('END_QUERY')">Nein (Sieg nach Nachwurf)</button>
            </div>
          </template>

          <template v-else-if="pendingConclusion.step === 'END_QUERY'">
            <p class="text-light mb-4 fs-5">Soll das Spiel jetzt <strong>final beendet</strong> werden?</p>
            <div class="d-flex justify-content-center gap-3">
              <button class="btn btn-lg btn-success px-4 fw-bold" @click="finishConclusion(true)">Ja (Spiel abschließen)</button>
              <button class="btn btn-lg btn-outline-secondary px-4 fw-bold" @click="finishConclusion(false)">Nein (Weiterspielen)</button>
            </div>
          </template>

          <button v-if="pendingConclusion.step !== 'NACHWURF'"
                  class="btn btn-sm btn-outline-secondary mt-4"
                  @click="conclusionBack">← Zurück</button>
          <button v-else
                  class="btn btn-sm btn-outline-secondary mt-4"
                  @click="pendingConclusion = null">Abbrechen</button>
        </div>

        <!-- ── Match beendet ── -->
        <div v-else-if="matchState?.winner"
             class="flex-grow-1 d-flex flex-column align-items-center justify-content-center text-center py-5">
          <div class="fs-1 mb-3">🏆</div>
          <h4 class="mb-1">{{ matchState.winner }} gewinnt!</h4>
          <p class="text-secondary small mt-2">Warte auf die nächste Spielzuweisung…</p>
        </div>

        <!-- ── Cup Controls ── -->
        <div v-else>
          <MatchTableControls
            :tournament-id="tournamentId"
            :match-id="String(assignment.match_id)"
            :team1-name="assignment.team1"
            :team2-name="assignment.team2"
            :team1-players="teamPlayerLabel(assignment.team1)"
            :team2-players="teamPlayerLabel(assignment.team2)"
            :is10-cups="cupsTarget === 10"
            :cups-state-team1="cupsState1"
            :cups-state-team2="cupsState2"
            :team1-rerack-used="matchState?.team1_rerack_used ?? false"
            :team2-rerack-used="matchState?.team2_rerack_used ?? false"
            @cup-hit="onCupHit"
            @undo="onUndo"
            @rerack="onRerack"
            @forfeit="onForfeit"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { api, createWebSocket } from '../api.js'
import MatchTableControls from '../components/MatchTableControls.vue'

const auth   = useAuthStore()
const router = useRouter()

// ── State ─────────────────────────────────────────────────────────────────────
const tournamentId       = ref(null)
const tournamentName     = ref('')
const tournamentData     = ref(null)
const teamPlayers        = ref({})       // { [teamName]: { player1, player2 } }
const tournaments        = ref([])
const loadingTournaments = ref(false)
const assignment         = ref(null)
const matchState         = ref(null)
const wsConnected        = ref(false)
let   ws                 = null
let   pollTimer          = null

// ── Overlays ──────────────────────────────────────────────────────────────────
const pendingShooter  = ref(null)
const selectedPlayer  = ref(null)
const pendingConclusion = ref(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const cupsTarget = computed(() => {
  const v = tournamentData.value?.cupsPerGame ?? tournamentData.value?.cups_per_game ?? 6
  return Number(v) || 6
})

const cupsState1 = computed(() => {
  const s = matchState.value?.cups_state_team1
  return s?.length ? s : Array(cupsTarget.value).fill(true)
})
const cupsState2 = computed(() => {
  const s = matchState.value?.cups_state_team2
  return s?.length ? s : Array(cupsTarget.value).fill(true)
})

const overtimeRemainingCups = computed(() => {
  if (!pendingShooter.value || pendingShooter.value.mode !== 'overtime_credit') return 0
  const total = pendingShooter.value.bonusCupCount || 0
  return total - (pendingShooter.value.bonusP1 || 0) - (pendingShooter.value.bonusP2 || 0)
})

const isOvertimeAllocationComplete = computed(() => {
  if (!pendingShooter.value) return false
  return overtimeRemainingCups.value === 0
})

// ── Helpers ───────────────────────────────────────────────────────────────────
function clampInt(v, min, max) {
  const n = parseInt(v, 10)
  return Math.max(min, Math.min(max, Number.isFinite(n) ? n : 0))
}
function safeNum(v) { const n = Number(v); return Number.isFinite(n) ? n : 0 }

function applyWinnerRule(m) {
  const a = safeNum(m.cups_team1), b = safeNum(m.cups_team2)
  const target = m.is_overtime ? cupsTarget.value + 3 : cupsTarget.value
  if (a >= target || b >= target) {
    if (a !== b) m.winner = a > b ? m.team1 : m.team2
  } else if (a === b) {
    m.winner = null
  }
}

function resolveTeamPlayers(teamName) {
  if (!teamName) return { p1: null, p2: null }
  const key = Object.keys(teamPlayers.value).find(k => k.trim().toLowerCase() === teamName.trim().toLowerCase())
  const p = teamPlayers.value[key ?? teamName] ?? {}
  return { p1: p.player1 || null, p2: p.player2 || null }
}

function teamPlayerLabel(teamName) {
  const { p1, p2 } = resolveTeamPlayers(teamName)
  return [p1, p2].filter(Boolean).join(' / ')
}

function getStandingCups(m, teamKey) {
  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  if (Array.isArray(m?.[stateKey]) && m[stateKey].length)
    return m[stateKey].filter(Boolean).length
  const hits = teamKey === 'team1' ? safeNum(m?.cups_team2) : safeNum(m?.cups_team1)
  return Math.max(0, cupsTarget.value - hits)
}

function buildFrontOvertimeState(size) {
  const state = Array(size).fill(false)
  if (size >= 10) { [9, 7, 8].forEach(i => { if (i < size) state[i] = true }); return state }
  if (size >= 6)  { [5, 3, 4].forEach(i => { if (i < size) state[i] = true }); return state }
  for (let i = Math.max(0, size - 3); i < size; i++) state[i] = true
  return state
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(async () => {
  loadingTournaments.value = true
  try {
    const data = await api.tournaments.list()
    tournaments.value = (Array.isArray(data) ? data : (data.results ?? []))
      .filter(t => ['group', 'playin', 'ko'].includes(t.current_phase ?? t.currentPhase ?? t.status))
  } catch { tournaments.value = [] }
  finally  { loadingTournaments.value = false }
})

onUnmounted(() => { _disconnect(); if (pollTimer) clearInterval(pollTimer) })

// ── Tournament selection ──────────────────────────────────────────────────────
function selectTournament(id) {
  tournamentId.value = id
  const t = tournaments.value.find(t => t.id === id)
  tournamentName.value = t?.name ?? `#${id}`
  if (t) tournamentData.value = t
  _connect(id)
  pollTimer = setInterval(_fetchAssignment, 5000)
  _fetchAssignment()
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function _connect(id) {
  _disconnect()
  ws = createWebSocket(id, auth.accessToken, null)
  ws.onopen    = () => { wsConnected.value = true }
  ws.onmessage = _handleMessage
  ws.onclose   = () => { wsConnected.value = false }
  ws.onerror   = (e) => console.error('Referee WS error', e)
}
function _disconnect() {
  if (ws) { ws.close(); ws = null }
  wsConnected.value = false
}

function _handleMessage(e) {
  try {
    const msg = JSON.parse(e.data)
    if (msg.type === 'assignment.updated') { _applyAssignment(msg.data); return }
    const data = msg.data
    if (!data) return
    if (data.tournament) tournamentData.value = data.tournament
    if (data.team_players) teamPlayers.value = { ...teamPlayers.value, ...data.team_players }
    // Don't overwrite overlays with WS updates
    if (pendingShooter.value || pendingConclusion.value) return
    if (assignment.value) _syncMatchFromState(data)
  } catch {}
}

// ── Assignment ────────────────────────────────────────────────────────────────
async function _fetchAssignment() {
  if (!tournamentId.value) return
  try {
    const res = await api.tournaments.myAssignment(tournamentId.value)
    _applyAssignment(res.assignment)
  } catch {}
}

function _applyAssignment(data) {
  if (!data) { assignment.value = null; matchState.value = null; return }
  assignment.value = data
  if (!matchState.value || matchState.value.id !== data.match_id) {
    matchState.value = _defaultMatchState(data)
    _fetchMatchState(data.match_id)
  }
}

function _defaultMatchState(a) {
  const n = cupsTarget.value
  return {
    id: a.match_id, team1: a.team1, team2: a.team2,
    winner: null, status: a.status, is_overtime: false,
    cups_team1: 0, cups_team2: 0,
    cups_state_team1: Array(n).fill(true),
    cups_state_team2: Array(n).fill(true),
    team1_rerack_used: false, team2_rerack_used: false,
    history_team1: [], history_team2: [],
    hit_history_team1: [], hit_history_team2: [],
    phase: a.phase, group_name: a.group_name,
    ko_round: a.ko_round, ko_bracket_type: a.ko_bracket_type, ko_match_index: a.ko_match_index,
  }
}

async function _fetchMatchState(matchId) {
  try {
    const state = await api.tournaments.loadAllData(tournamentId.value)
    if (state.tournament) tournamentData.value = state.tournament
    if (state.team_players) teamPlayers.value = state.team_players
    _syncMatchFromState(state, matchId)
  } catch {}
}

function _syncMatchFromState(state, matchId) {
  const id = matchId ?? assignment.value?.match_id
  if (!id) return
  if (state.group_phase?.matches) {
    for (const matches of Object.values(state.group_phase.matches)) {
      const m = (matches || []).find(m => m.id === id)
      if (m) { matchState.value = { ...m }; return }
    }
  }
  if (state.ko_phase?.rounds) {
    for (const round of state.ko_phase.rounds) {
      const m = (round.matches || []).find(m => m.id === id)
      if (m) { matchState.value = { ...m }; return }
    }
  }
  if (state.match?.id === id) matchState.value = { ...(matchState.value||{}), ...state.match }
  if (state.id === id && state.cups_team1 !== undefined) matchState.value = { ...(matchState.value||{}), ...state }
}

// ── Cup hit flow ──────────────────────────────────────────────────────────────
function onCupHit({ teamKey, cupIndex }) {
  if (!matchState.value || !assignment.value) return
  const m = matchState.value
  // Shooter is the team that did NOT have cups hit
  const shooterTeamKey  = teamKey === 'team1' ? 'team2' : 'team1'
  const shooterTeamName = shooterTeamKey === 'team1' ? m.team1 : m.team2
  const { p1, p2 } = resolveTeamPlayers(shooterTeamName)

  if (!p1 && !p2) {
    _doActualCupHit(teamKey, cupIndex, null, shooterTeamName)
    return
  }
  pendingShooter.value = { mode: 'cup_hit', teamKey, cupIndex, teamName: shooterTeamName, p1, p2 }
  selectedPlayer.value = null
}

function _doActualCupHit(teamKey, cupIndex, shooterName, shooterTeam) {
  if (!matchState.value) return
  const m = { ...matchState.value }
  const stateKey   = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  const histKey    = teamKey === 'team1' ? 'history_team1' : 'history_team2'
  const hitHistKey = teamKey === 'team1' ? 'hit_history_team1' : 'hit_history_team2'
  const cupsField  = teamKey === 'team2' ? 'cups_team1' : 'cups_team2'

  const state = [...(m[stateKey]?.length ? m[stateKey] : Array(cupsTarget.value).fill(true))]
  state[cupIndex] = false
  m[stateKey] = state

  m[hitHistKey] = [...(m[hitHistKey] || []), cupIndex]
  m[histKey]    = [...(m[histKey] || []), { type: 'hit', idx: cupIndex }]
  m[cupsField]  = clampInt((m[cupsField] || 0) + 1, 0, cupsTarget.value + 3)

  const standingCups = state.filter(v => v).length
  matchState.value = { ...m }

  if (standingCups === 0) {
    if (m.is_overtime) {
      pendingConclusion.value = { step: 'END_QUERY', history: ['END_QUERY'], teamKey }
    } else {
      pendingConclusion.value = { step: 'NACHWURF', history: ['NACHWURF'], teamKey }
    }
  }

  _saveMatch({ action_type: 'cup_hit', team_key: teamKey, cup_index: cupIndex,
               player_name: shooterName, team_name: shooterTeam || (teamKey === 'team1' ? m.team2 : m.team1) })
}

// ── Shooter overlay ───────────────────────────────────────────────────────────
function confirmShooter() {
  if (!pendingShooter.value) return
  const { mode, teamKey, cupIndex, teamName } = pendingShooter.value

  if (mode === 'overtime_credit') {
    const allocs = []
    if (pendingShooter.value.p1 && (pendingShooter.value.bonusP1 || 0) > 0)
      allocs.push({ player_name: pendingShooter.value.p1, count: pendingShooter.value.bonusP1 })
    if (pendingShooter.value.p2 && (pendingShooter.value.bonusP2 || 0) > 0)
      allocs.push({ player_name: pendingShooter.value.p2, count: pendingShooter.value.bonusP2 })
    const saved = { ...pendingShooter.value }
    pendingShooter.value = null; selectedPlayer.value = null
    _doApplyOvertime(saved.teamKey, teamName, saved.bonusCupCount, allocs)
    return
  }

  if (!selectedPlayer.value) return
  const player = selectedPlayer.value
  pendingShooter.value = null; selectedPlayer.value = null
  _doActualCupHit(teamKey, cupIndex, player, teamName)
}

function cancelShooter() { pendingShooter.value = null; selectedPlayer.value = null }

function adjustOvertimeAlloc(who, delta) {
  if (!pendingShooter.value) return
  const key = who === 'p1' ? 'bonusP1' : 'bonusP2'
  const cur = pendingShooter.value[key] || 0
  const next = clampInt(cur + delta, 0, (pendingShooter.value.bonusCupCount || 0))
  pendingShooter.value = { ...pendingShooter.value, [key]: next }
}

// ── Conclusion flow ───────────────────────────────────────────────────────────
function conclusionStep(newStep) {
  if (!pendingConclusion.value) return
  pendingConclusion.value = {
    ...pendingConclusion.value,
    step: newStep,
    history: [...(pendingConclusion.value.history || []), newStep],
  }
}

function conclusionBack() {
  if (!pendingConclusion.value) return
  const h = [...(pendingConclusion.value.history || [])]
  if (h.length <= 1) { pendingConclusion.value = null; return }
  h.pop()
  pendingConclusion.value = { ...pendingConclusion.value, step: h[h.length - 1], history: h }
}

function conclusionOvertime() {
  if (!pendingConclusion.value || !matchState.value) return
  const { teamKey } = pendingConclusion.value
  const m = matchState.value
  const overtimeTeamName  = teamKey === 'team1' ? m.team1 : m.team2
  const opponentTeamKey   = teamKey === 'team1' ? 'team2' : 'team1'
  const remainingOpponentCups = getStandingCups(m, opponentTeamKey)
  const { p1, p2 } = resolveTeamPlayers(overtimeTeamName)

  pendingConclusion.value = null

  if (remainingOpponentCups > 0 && (p1 || p2)) {
    pendingShooter.value = {
      mode: 'overtime_credit', teamKey,
      teamName: overtimeTeamName, p1, p2,
      bonusCupCount: remainingOpponentCups,
      bonusP1: p1 && !p2 ? remainingOpponentCups : 0,
      bonusP2: p2 && !p1 ? remainingOpponentCups : 0,
    }
    return
  }
  _doApplyOvertime(teamKey, overtimeTeamName, remainingOpponentCups, [])
}

function _doApplyOvertime(teamKey, overtimeTeamName, creditCount, allocations) {
  if (!matchState.value) return
  const m = { ...matchState.value }
  if (creditCount > 0) {
    const sf = teamKey === 'team1' ? 'cups_team1' : 'cups_team2'
    m[sf] = clampInt(safeNum(m[sf]) + creditCount, 0, cupsTarget.value)
  }
  m.cups_state_team1 = buildFrontOvertimeState(cupsTarget.value)
  m.cups_state_team2 = buildFrontOvertimeState(cupsTarget.value)
  m.winner = null
  m.is_overtime = true
  matchState.value = m

  const eventData = overtimeTeamName && allocations.length
    ? { action_type: 'overtime_credit', team_name: overtimeTeamName,
        credit_count: creditCount, credit_allocations: allocations }
    : { action_type: 'overtime' }
  _saveMatch(eventData)
}

function finishConclusion(actuallyFinish) {
  if (!pendingConclusion.value || !matchState.value) return
  if (actuallyFinish) {
    const m = { ...matchState.value }
    const a = safeNum(m.cups_team1), b = safeNum(m.cups_team2)
    if (a === b) return
    m.winner = a > b ? m.team1 : m.team2
    m.status = 'done'
    m.table_no = null
    matchState.value = m
    _saveMatch({ action_type: 'finished' })
  }
  pendingConclusion.value = null
}

// ── Undo ──────────────────────────────────────────────────────────────────────
function onUndo({ teamKey }) {
  if (!matchState.value) return
  const m = { ...matchState.value }
  const stateKey   = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  const histKey    = teamKey === 'team1' ? 'history_team1' : 'history_team2'
  const hitHistKey = teamKey === 'team1' ? 'hit_history_team1' : 'hit_history_team2'

  const history = [...(m[histKey] || [])]
  if (!history.length) return
  const last = history.pop()
  m[histKey] = history

  const cups = [...(m[stateKey]?.length ? m[stateKey] : Array(cupsTarget.value).fill(true))]

  if (last.type === 'hit') {
    cups[last.idx] = true
    const hh = [...(m[hitHistKey] || [])]
    if (hh[hh.length - 1] === last.idx) hh.pop()
    m[hitHistKey] = hh
    const cupsField = teamKey === 'team2' ? 'cups_team1' : 'cups_team2'
    m[cupsField] = clampInt((m[cupsField] || 0) - 1, 0, cupsTarget.value)
  } else if (last.type === 'rerack') {
    cups.splice(0, cups.length, ...last.state)
    if (teamKey === 'team1') m.team1_rerack_used = false
    if (teamKey === 'team2') m.team2_rerack_used = false
  }

  m[stateKey] = cups
  m.winner = null; m.status = 'pending'
  applyWinnerRule(m)
  matchState.value = m
  _saveMatch({ action_type: 'undo', team_key: teamKey })
}

// ── Rerack ────────────────────────────────────────────────────────────────────
function onRerack({ teamKey, newState }) {
  if (!matchState.value) return
  const m = { ...matchState.value }
  const stateKey  = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  const histKey   = teamKey === 'team1' ? 'history_team1' : 'history_team2'
  const rerackKey = teamKey === 'team1' ? 'team1_rerack_used' : 'team2_rerack_used'
  const prev      = m[stateKey]?.length ? m[stateKey] : Array(cupsTarget.value).fill(true)
  m[histKey]   = [...(m[histKey] || []), { type: 'rerack', state: [...prev] }]
  m[stateKey]  = newState
  m[rerackKey] = true
  matchState.value = m
  _saveMatch({ action_type: 'rerack', team_key: teamKey })
}

function onForfeit({ teamKey }) {
  if (!matchState.value) return
  const m = { ...matchState.value }
  const losingTeamName = teamKey === 'team1' ? m.team1 : m.team2
  const winnerTeamName = teamKey === 'team1' ? m.team2 : m.team1
  if (!losingTeamName || !winnerTeamName) return

  m.winner = winnerTeamName
  m.status = 'done'
  m.table_no = null
  matchState.value = m
  pendingShooter.value = null
  selectedPlayer.value = null
  pendingConclusion.value = null

  _saveMatch({
    action_type: 'forfeit',
    team_key: teamKey,
    team_name: losingTeamName,
    winner_name: winnerTeamName,
  })
}

// ── API save ──────────────────────────────────────────────────────────────────
async function _saveMatch(eventData) {
  if (!assignment.value || !matchState.value || !tournamentId.value) return
  const m = matchState.value
  const a = assignment.value
  const payload = {
    id: a.match_id, team1: m.team1, team2: m.team2,
    winner: m.winner ?? null,
    cups_team1: safeNum(m.cups_team1),
    cups_team2: safeNum(m.cups_team2),
    cups_state_team1: m.cups_state_team1 ?? [],
    cups_state_team2: m.cups_state_team2 ?? [],
    hit_history_team1: m.hit_history_team1 ?? [],
    hit_history_team2: m.hit_history_team2 ?? [],
    history_team1: m.history_team1 ?? [],
    history_team2: m.history_team2 ?? [],
    team1_rerack_used: m.team1_rerack_used ?? false,
    team2_rerack_used: m.team2_rerack_used ?? false,
    is_overtime: m.is_overtime ?? false,
    event_data: eventData,
  }
  try {
    if (a.phase === 'ko') {
      await api.tournaments.koMatch(tournamentId.value, { ...payload, match_id: a.match_id })
    } else {
      await api.tournaments.groupMatch(tournamentId.value, { ...payload, group_name: a.group_name })
    }
  } catch (e) { console.error('Save match failed', e) }
}

// ── Auth ──────────────────────────────────────────────────────────────────────
function handleLogout() { _disconnect(); auth.logout(); router.push('/login') }
</script>

<style scoped>
.waiting-pulse { position: relative; width: 80px; height: 80px; }
.waiting-circle {
  position: absolute; inset: 0; border-radius: 50%;
  border: 3px solid #6c757d;
  animation: pulse 1.8s ease-in-out infinite;
}
.waiting-circle::before {
  content: ''; position: absolute; inset: 10px; border-radius: 50%;
  background: #ffc107; opacity: 0.6;
  animation: pulse 1.8s ease-in-out infinite 0.4s;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50%       { transform: scale(1.15); opacity: 0.4; }
}

.referee-logo {
  width: 34px;
  height: 34px;
  object-fit: contain;
}
</style>
