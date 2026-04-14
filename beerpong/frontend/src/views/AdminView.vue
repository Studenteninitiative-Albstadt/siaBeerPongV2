<template>
  <div class="app-wrapper bg-dark text-light min-vh-100">
    <HeaderBar
      :has-active="!!tournament?.id"
      :tournament-name="tournamentName"
      :tournament-phase="tournamentPhase"
      @create-new="handleCreateNew"
      @open-loader="toggleLoadPanel"
    >
      <!-- Auth info slot in HeaderBar (falls vorhanden) -->
      <template #extra>
        <span class="text-secondary small me-3">{{ auth.username }}</span>
        <button class="btn btn-sm btn-outline-secondary" @click="handleLogout">Abmelden</button>
      </template>
    </HeaderBar>

    <main class="container py-5">
      <InfoPanel v-if="step === 0 && !showLoad" class="mb-4" />

      <!-- Tournament list -->
      <div v-if="showLoad" class="card bg-black border-secondary text-light mb-4">
        <div class="card-header bg-black border-secondary d-flex justify-content-between align-items-center">
          <strong>Vorhandene Turniere</strong>
          <button class="btn btn-sm btn-outline-light" @click="fetchTournamentsList">Neu laden</button>
        </div>
        <div class="card-body text-light">
          <div v-if="loadingList" class="text-secondary">Lade…</div>
          <div v-else-if="tournamentsList.length === 0" class="text-secondary">Keine Turniere vorhanden.</div>
          <div v-else class="list-group">
            <div v-for="t in tournamentsList" :key="t.id"
                 class="list-group-item bg-black text-light border-secondary d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-bold text-light">{{ t.name }} <small class="text-secondary">(#{{ t.id }})</small></div>
                <div class="small text-secondary">
                  Teams: {{ t.participant_count ?? t.participantCount }} ·
                  Modus: {{ t.mode }} · Phase: {{ t.current_phase ?? t.currentPhase ?? 'group' }}
                </div>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-success"       @click="loadTournament(t.id)">Laden</button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteTournament(t.id)">Löschen</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <TournamentWizard
        v-if="step === 0 || step === 1 || step === 2 || step === 3"
        :step="step"
        :tournament="tournament"
        :teams="teams"
        @update:step="step = $event"
        @update:tournament="tournament = $event"
        @update:teams="teams = $event"
        @update:team-players="teamPlayers = $event"
        @finish="handleFinish"
        @open-load-dialog="toggleLoadPanel"
      />

      <GroupsView
        v-else-if="step === 4"
        :tournament-id="tournament?.id"
        :tournament="tournament"
        :teams="teams"
        :team-players="teamPlayers"
        @back="step = 0"
        @create-ko="handleCreateKoFromGroups"
      />

      <KnockoutPreview
        v-else-if="step === 6"
        :teams="koPreviewTeams"
        :ko-size="targetKoSize || null"
        @cancel="handlePreviewCancel"
        @confirm="handleKoPreviewConfirm"
      />

      <PlayInView
        v-else-if="step === 7"
        :tournament-id="tournament?.id"
        :auto-qualified="pendingQualified"
        :ko-size="targetKoSize || null"
        :candidates="playInCandidates"
        :matches="playInMatches"
        :rage-cage="rageCageGroups"
        :policy-notes="policyNotes"
        @back="step = 4"
        @to-ko="handlePlayInToKo"
        @create-ko="handlePlayInToKo"
      />

      <KnockoutView
        v-else-if="step === 5"
        :tournament-id="tournament?.id"
        :teams="koPreviewTeams"
        :ko-size="targetKoSize || null"
        @back="handleKoBack"
        @saved="handleKoSaved"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useTournamentStore } from '../stores/tournament.js'
import { api } from '../api.js'

import HeaderBar        from '../components/HeaderBar.vue'
import InfoPanel        from '../components/InfoPanel.vue'
import TournamentWizard from '../components/TournamentWizard.vue'
import GroupsView       from '../components/GroupsView/GroupsView.vue'
import KnockoutView     from '../components/KnockoutView.vue'
import PlayInView       from '../components/PlayInView.vue'
import KnockoutPreview  from '../components/KnockoutPreview.vue'

const auth   = useAuthStore()
const store  = useTournamentStore()
const router = useRouter()

// ── Local UI state (same shape as old App.vue) ──────────────────────────────
const step         = ref(0)
const showLoad     = ref(false)
const loadingList  = ref(false)
const tournamentsList = ref([])

const tournament = ref({ id: null, name: 'Neues Turnier', mode: 'groups',
  participantCount: 8, cupsPerGame: 6, finaleWith10Cups: false, current_phase: 'group' })
const teams = ref([])
const teamPlayers = ref({}) // { [teamName]: { player1, player2 } }

const tournamentName  = computed(() => tournament.value?.name ?? ('#' + (tournament.value?.id ?? '')))
const tournamentPhase = computed(() => tournament.value?.current_phase ?? tournament.value?.currentPhase ?? 'group')

const koPreviewTeams  = ref([])
const pendingQualified = ref([])
const cameFromPlayIn  = ref(false)
const targetKoSize    = ref(null)
const playInMatches   = ref([])
const rageCageGroups  = ref([])
const policyNotes     = ref([])
const playInCandidates = ref([])

// ── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => fetchTournamentsList().catch(() => {}))
onUnmounted(() => store.disconnect())

// ── Auth ─────────────────────────────────────────────────────────────────────
function handleLogout() {
  auth.logout()
  router.push('/login')
}

// ── Tournament list ───────────────────────────────────────────────────────────
function handleCreateNew() {
  showLoad.value = false
  step.value = 0
}

function toggleLoadPanel() {
  showLoad.value = !showLoad.value
  if (showLoad.value) fetchTournamentsList()
}

async function fetchTournamentsList() {
  loadingList.value = true
  try {
    const data = await api.tournaments.list()
    tournamentsList.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch { tournamentsList.value = [] }
  finally  { loadingList.value = false }
}

async function loadTournament(id) {
  try {
    const data = await api.tournaments.loadAllData(id)
    const t = data.tournament ?? {}
    tournament.value = {
      id: t.id, name: t.name, mode: t.mode ?? 'groups',
      participantCount: t.participantCount ?? t.participant_count ?? 8,
      cupsPerGame: t.cupsPerGame ?? t.cups_per_game ?? 6,
      finaleWith10Cups: t.finaleWith10Cups ?? t.finale_with_10_cups ?? false,
      current_phase: t.currentPhase ?? t.current_phase ?? 'group',
    }

    let loadedTeams = []
    let loadedPlayers = {}
    if (Array.isArray(data.teams)) {
      for (const t of data.teams) {
        if (typeof t === 'object' && t !== null) {
          const n = t.name || t.teamName || ''
          if (n) {
            loadedTeams.push(n)
            loadedPlayers[n] = { player1: t.player1 || '', player2: t.player2 || '' }
          }
        } else if (typeof t === 'string') {
          loadedTeams.push(t)
        }
      }
    }
    teams.value = loadedTeams
    teamPlayers.value = Object.keys(data.team_players || {}).length > 0 ? data.team_players : loadedPlayers

    // Connect WebSocket for real-time updates
    store.connect(id)

    const phase = tournament.value.current_phase
    if (phase === 'playin') {
      const pi = data.playin ?? {}
      pendingQualified.value = pi.direct_qualified_labels ?? pi.direct_qualified ?? []
      playInMatches.value    = pi.playin_matches ?? []
      rageCageGroups.value   = pi.rage_cage_groups ?? []
      policyNotes.value      = pi.policy_notes ?? []
      targetKoSize.value     = pi.ko_size ?? null
      playInCandidates.value = pi.ranking_candidates ?? []
      cameFromPlayIn.value   = true
      step.value = 7
    } else if (phase === 'ko') {
      cameFromPlayIn.value = false
      targetKoSize.value   = data.ko_phase?.ko_size ?? null
      koPreviewTeams.value = []
      step.value = 5
    } else {
      step.value = 4
    }
    showLoad.value = false
  } catch (e) { console.error('loadTournament failed:', e) }
}

async function deleteTournament(id) {
  try {
    await api.tournaments.delete(id)
    tournamentsList.value = tournamentsList.value.filter(t => t.id !== id)
    if (tournament.value?.id === id) {
      step.value = 0
      _resetTournamentState()
    }
  } catch (e) { console.error('deleteTournament failed:', e) }
}

async function handleFinish(finalTournament) {
  try {
    const body = {
      name: finalTournament.name ?? 'Neues Turnier',
      mode: 'groups',
      participantCount: +finalTournament.participantCount || 8,
      cupsPerGame:      +finalTournament.cupsPerGame      || 6,
      finaleWith10Cups: !!finalTournament.finaleWith10Cups,
    }
    const created = await api.tournaments.create(body)
    const tId = created.id
    if (!tId) throw new Error('no id')

    const teamList = Array.isArray(finalTournament.teams) ? finalTournament.teams : []
    const players  = finalTournament.teamPlayers ?? {}
    if (teamList.length) {
      const teamsPayload = teamList.map(name => ({
        name,
        player1: players[name]?.player1 ?? '',
        player2: players[name]?.player2 ?? '',
      }))
      await api.tournaments.saveTeams(tId, teamsPayload).catch(() => {})
    }
    teamPlayers.value = players

    tournament.value = {
      id: tId, name: created.name ?? body.name, mode: created.mode ?? 'groups',
      participantCount: created.participantCount ?? body.participantCount,
      cupsPerGame:      created.cupsPerGame      ?? body.cupsPerGame,
      finaleWith10Cups: created.finaleWith10Cups ?? body.finaleWith10Cups,
      current_phase: created.currentPhase ?? 'group',
    }
    teams.value = teamList.slice()
    step.value  = 4

    store.connect(tId)
    fetchTournamentsList().catch(() => {})
  } catch (e) { console.error('handleFinish failed:', e) }
}

// ── KO / Play-In flow (identical logic to old App.vue) ───────────────────────
function pow2KoSize(q) {
  for (const k of [4, 8, 16, 32, 64, 128]) if (k >= q) return k
  return q
}
function pairTeamsToMatches(list) {
  const out = []
  for (let i = 0; i < list.length; i += 2) {
    if (list[i] && list[i + 1]) out.push({ team1: list[i], team2: list[i + 1], winner: null })
  }
  return out
}

function handleCreateKoFromGroups({ tables, playIn, cupsTarget, koSize }) {
  const topTwos = Object.values(tables ?? {}).flatMap(rows => rows.slice(0, 2).map(r => r.name))
  pendingQualified.value = Array.from(new Set(topTwos))
  targetKoSize.value     = koSize ?? playIn?.ko_size ?? null
  playInCandidates.value = playIn?.ranking_candidates ?? []
  playInMatches.value    = playIn?.playin_matches ?? []
  rageCageGroups.value   = playIn?.rage_cage_groups ?? []
  policyNotes.value      = playIn?.policy_notes ?? []

  if (!playIn?.playin_needed) {
    koPreviewTeams.value = [...pendingQualified.value, ...(playIn?.auto_advanced ?? [])]
    step.value = 6
  } else if (playInMatches.value.length || rageCageGroups.value.length || playInCandidates.value.length) {
    step.value = 7
  } else {
    koPreviewTeams.value = pendingQualified.value.slice()
    step.value = 6
  }
}

function handlePlayInToKo(payload) {
  koPreviewTeams.value = (payload?.qualified ?? []).slice()
  targetKoSize.value   = payload?.koSize ?? pow2KoSize(koPreviewTeams.value.length)
  step.value = 6
}

async function handleKoPreviewConfirm({ teams: finalTeams, koSize }) {
  koPreviewTeams.value = finalTeams.slice()
  targetKoSize.value   = koSize ?? pow2KoSize(finalTeams.length)
  step.value = 5
  if (tournament.value?.id) {
    try {
      const roundName = finalTeams.length === 8 ? 'Viertelfinale'
                      : finalTeams.length === 4 ? 'Halbfinale' : 'KO'
      await api.tournaments.saveKoBracket(tournament.value.id, {
        rounds: [{ round_name: roundName, bracket_type: 'main', matches: pairTeamsToMatches(finalTeams) }]
      })
      await api.tournaments.update(tournament.value.id, { currentPhase: 'ko' })
      tournament.value.current_phase = 'ko'
    } catch (e) { console.warn('KO speichern fehlgeschlagen:', e) }
  }
}

function handlePreviewCancel() { step.value = cameFromPlayIn.value ? 7 : 4 }
function handleKoBack()        { step.value = cameFromPlayIn.value ? 6 : 4 }
function handleKoSaved()       { /* noop */ }

function _resetTournamentState() {
  tournament.value = { id: null, name: 'Neues Turnier', mode: 'groups',
    participantCount: 8, cupsPerGame: 6, finaleWith10Cups: false, current_phase: 'group' }
  teams.value          = []
  teamPlayers.value    = {}
  koPreviewTeams.value = []
  pendingQualified.value = []
  playInMatches.value  = []
  rageCageGroups.value = []
  policyNotes.value    = []
  targetKoSize.value   = null
  playInCandidates.value = []
}
</script>

<style scoped>
.app-wrapper {
  background: radial-gradient(circle at top, #1f1f1f 0%, #0d0d0d 55%, #000 100%);
}
.list-group-item.bg-black:hover {
  background-color: #111 !important;
}
</style>
