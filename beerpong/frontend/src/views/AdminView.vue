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
        :slots="koPreviewSlots"
        @cancel="handlePreviewCancel"
        @confirm="handleKoPreviewConfirm"
      />

      <PlayInView
        v-else-if="step === 7"
        :tournament-id="tournament?.id"
        :auto-qualified="pendingQualified"
        :auto-qualified-slots="pendingQualifiedSlots"
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
const koPreviewSlots  = ref([])
const pendingQualified = ref([])
const pendingQualifiedSlots = ref([])
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
      pendingQualifiedSlots.value = normalizePreviewSlots(
        pi.direct_qualified_slots ?? pi.direct_qualified_labels ?? pi.direct_qualified,
        'Direkt qualifiziert'
      )
      playInMatches.value    = pi.playin_matches ?? []
      rageCageGroups.value   = pi.rage_cage_groups ?? []
      policyNotes.value      = pi.policy_notes ?? []
      targetKoSize.value     = pi.ko_size ?? null
      playInCandidates.value = pi.ranking_candidates ?? []
      koPreviewSlots.value   = []
      cameFromPlayIn.value   = true
      step.value = 7
    } else if (phase === 'ko_preview') {
      const pi = data.playin ?? {}
      const preview = data.ko_preview ?? {}
      koPreviewSlots.value = normalizePreviewSlots(preview.slots, 'KO')
      koPreviewTeams.value = koPreviewSlots.value.map(slot => slot.teamName).filter(Boolean)
      targetKoSize.value   = preview.ko_size ?? preview.koSize ?? null
      cameFromPlayIn.value = preview.source === 'playin'
      pendingQualified.value = pi.direct_qualified_labels ?? pi.direct_qualified ?? []
      pendingQualifiedSlots.value = normalizePreviewSlots(
        pi.direct_qualified_slots ?? pi.direct_qualified_labels ?? pi.direct_qualified,
        'Direkt qualifiziert'
      )
      playInMatches.value    = pi.playin_matches ?? []
      rageCageGroups.value   = pi.rage_cage_groups ?? []
      policyNotes.value      = pi.policy_notes ?? []
      playInCandidates.value = pi.ranking_candidates ?? []
      step.value = 6
    } else if (phase === 'ko') {
      cameFromPlayIn.value = false
      targetKoSize.value   = data.ko_phase?.ko_size ?? null
      koPreviewTeams.value = []
      koPreviewSlots.value = []
      pendingQualifiedSlots.value = []
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
      await api.tournaments.saveTeams(tId, teamsPayload)
      const persistedTeams = await api.tournaments.loadTeams(tId).catch(() => ({ teams: [] }))
      const persistedTeamPlayers = Object.fromEntries(
        (persistedTeams?.teams || []).map(team => [
          team.name,
          {
            player1: team.player1 || '',
            player2: team.player2 || '',
          },
        ])
      )
      const hasMismatch = teamList.some(name =>
        (persistedTeamPlayers[name]?.player1 || '') !== (players[name]?.player1 || '') ||
        (persistedTeamPlayers[name]?.player2 || '') !== (players[name]?.player2 || '')
      )
      if (hasMismatch) {
        throw new Error('team player persistence failed')
      }
    }
    teamPlayers.value = players

    await store.load(tId)

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

function normalizeGroupLabel(groupName) {
  const raw = String(groupName ?? '').trim()
  if (!raw) return 'Gruppe'
  return /^gruppe\b/i.test(raw) ? raw : `Gruppe ${raw}`
}

function normalizePreviewSlot(slot, idx, fallbackPrefix = 'Slot') {
  if (!slot) return null
  if (typeof slot === 'string') {
    return {
      id: `${fallbackPrefix.toLowerCase().replace(/\s+/g, '-')}-${idx}`,
      sourceLabel: slot,
      teamName: slot,
      isBye: false,
    }
  }
  const teamName = slot.teamName || slot.team || ''
  return {
    id: slot.id ?? `${fallbackPrefix.toLowerCase().replace(/\s+/g, '-')}-${idx}`,
    sourceLabel: slot.sourceLabel || slot.label || teamName || `${fallbackPrefix} ${idx + 1}`,
    teamName,
    isBye: !!slot.isBye,
  }
}

function normalizePreviewSlots(list, fallbackPrefix = 'Slot') {
  return (list || [])
    .map((slot, idx) => normalizePreviewSlot(slot, idx, fallbackPrefix))
    .filter(Boolean)
}

function buildDirectQualifiedSlots(tables) {
  const winners = []
  const runnersUp = []
  for (const [groupName, rows] of Object.entries(tables ?? {})) {
    const normalizedGroup = normalizeGroupLabel(groupName)
    if (rows?.[0]?.name) {
      winners.push({
        id: `direct-${groupName}-1`,
        sourceLabel: `Sieger ${normalizedGroup}`,
        teamName: rows[0].name,
      })
    }
    if (rows?.[1]?.name) {
      runnersUp.push({
        id: `direct-${groupName}-2`,
        sourceLabel: `2. ${normalizedGroup}`,
        teamName: rows[1].name,
      })
    }
  }

  const slots = []
  for (let i = 0; i < winners.length; i++) {
    slots.push(winners[i])
    const mirroredRunner = runnersUp[runnersUp.length - 1 - i]
    if (mirroredRunner) slots.push(mirroredRunner)
  }
  return slots
}

function buildAutoAdvancedSlots(autoAdvanced, rankingCandidates) {
  const rankedNames = (rankingCandidates || []).map(row => row?.name).filter(Boolean)
  return (autoAdvanced || [])
    .filter(Boolean)
    .map((teamName, idx) => {
      const rankingIndex = rankedNames.findIndex(name => name === teamName)
      return {
        id: `ranking-${idx}`,
        sourceLabel: rankingIndex >= 0 ? `Ranking ${rankingIndex + 1}` : `Wildcard ${idx + 1}`,
        teamName,
      }
    })
}

function buildPlayInWinnerSlots(matches) {
  return (matches || [])
    .map((match, idx) => {
      const winner = typeof match === 'string' ? match : match?.winner
      if (!winner) return null
      return {
        id: `playin-${idx}`,
        sourceLabel: `Sieger Play-In ${idx + 1}`,
        teamName: winner,
      }
    })
    .filter(Boolean)
}

async function persistKoPreview({ slots, koSize, source, phase = 'ko_preview' }) {
  if (!tournament.value?.id) return
  try {
    await api.tournaments.saveKoPreview(tournament.value.id, {
      slots,
      koSize,
      teams: (slots || []).map(slot => slot.teamName).filter(Boolean),
      source,
      phase,
    })
    await api.tournaments.update(tournament.value.id, { currentPhase: phase })
    tournament.value.current_phase = phase
  } catch (e) {
    console.warn('KO-Vorschau speichern fehlgeschlagen:', e)
  }
}

async function handleCreateKoFromGroups({ tables, playIn, cupsTarget, koSize }) {
  const directSlots = buildDirectQualifiedSlots(tables)
  pendingQualifiedSlots.value = directSlots
  pendingQualified.value = directSlots.map(slot => slot.teamName)
  targetKoSize.value     = koSize ?? playIn?.ko_size ?? null
  playInCandidates.value = playIn?.ranking_candidates ?? []
  playInMatches.value    = playIn?.playin_matches ?? []
  rageCageGroups.value   = playIn?.rage_cage_groups ?? []
  policyNotes.value      = playIn?.policy_notes ?? []

  if (!playIn?.playin_needed) {
    const previewSlots = [
      ...directSlots,
      ...buildAutoAdvancedSlots(playIn?.auto_advanced ?? [], playIn?.ranking_candidates ?? []),
    ]
    koPreviewSlots.value = previewSlots
    koPreviewTeams.value = previewSlots.map(slot => slot.teamName).filter(Boolean)
    cameFromPlayIn.value = false
    await persistKoPreview({
      slots: previewSlots,
      koSize: targetKoSize.value,
      source: 'groups',
    })
    step.value = 6
  } else if (playInMatches.value.length || rageCageGroups.value.length || playInCandidates.value.length) {
    koPreviewSlots.value = []
    cameFromPlayIn.value = true
    step.value = 7
  } else {
    koPreviewSlots.value = directSlots.slice()
    koPreviewTeams.value = pendingQualified.value.slice()
    cameFromPlayIn.value = false
    await persistKoPreview({
      slots: koPreviewSlots.value,
      koSize: targetKoSize.value,
      source: 'groups',
    })
    step.value = 6
  }
}

async function handlePlayInToKo(payload) {
  const qualified = (payload?.qualified ?? []).slice()
  const explicitWinnerSlots = normalizePreviewSlots(payload?.previewSlots, 'Play-In')
  const winnerSlots = explicitWinnerSlots.length
    ? explicitWinnerSlots
    : buildPlayInWinnerSlots(payload?.playin_matches ?? [])
  const previewSlots = [...pendingQualifiedSlots.value, ...winnerSlots]
  const seenTeams = new Set(previewSlots.map(slot => slot.teamName).filter(Boolean))

  for (const teamName of qualified) {
    if (!teamName || seenTeams.has(teamName)) continue
    previewSlots.push({
      id: `fallback-${teamName}`,
      sourceLabel: 'Qualifiziert',
      teamName,
    })
    seenTeams.add(teamName)
  }

  koPreviewSlots.value = previewSlots
  koPreviewTeams.value = qualified
  targetKoSize.value   = payload?.koSize ?? pow2KoSize(koPreviewTeams.value.length)
  cameFromPlayIn.value = true
  await persistKoPreview({
    slots: previewSlots,
    koSize: targetKoSize.value,
    source: 'playin',
  })
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

async function handlePreviewCancel() {
  const fallbackPhase = cameFromPlayIn.value ? 'playin' : 'group'
  if (tournament.value?.id) {
    try {
      await api.tournaments.saveKoPreview(tournament.value.id, {
        slots: [],
        koSize: null,
        teams: [],
        source: cameFromPlayIn.value ? 'playin' : 'groups',
        phase: fallbackPhase,
      })
      tournament.value.current_phase = fallbackPhase
    } catch (e) {
      console.warn('KO-Vorschau zurücksetzen fehlgeschlagen:', e)
    }
  }
  step.value = cameFromPlayIn.value ? 7 : 4
}
function handleKoBack()        { step.value = cameFromPlayIn.value ? 6 : 4 }
function handleKoSaved()       { /* noop */ }

function _resetTournamentState() {
  tournament.value = { id: null, name: 'Neues Turnier', mode: 'groups',
    participantCount: 8, cupsPerGame: 6, finaleWith10Cups: false, current_phase: 'group' }
  teams.value          = []
  teamPlayers.value    = {}
  koPreviewTeams.value = []
  koPreviewSlots.value = []
  pendingQualified.value = []
  pendingQualifiedSlots.value = []
  playInMatches.value  = []
  rageCageGroups.value = []
  policyNotes.value    = []
  targetKoSize.value   = null
  playInCandidates.value = []
  cameFromPlayIn.value = false
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
