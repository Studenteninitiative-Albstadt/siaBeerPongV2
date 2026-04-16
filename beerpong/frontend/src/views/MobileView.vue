<template>
  <div class="min-vh-100 bg-dark text-light"
       style="background:radial-gradient(circle at top,#0d1b2a 0%,#0a0a0a 60%,#000 100%)">

    <!-- Invalid / Loading -->
    <div v-if="!valid && !loading"
         class="min-vh-100 d-flex align-items-center justify-content-center p-4">
      <div class="text-center">
        <div class="fs-1 mb-3">🚫</div>
        <h4 class="text-danger">Ungültiger Zugangslink</h4>
        <p class="text-secondary small">Scanne den QR-Code erneut am Beamer.</p>
      </div>
    </div>

    <div v-else-if="loading"
         class="min-vh-100 d-flex align-items-center justify-content-center">
      <div class="spinner-border text-light" role="status"></div>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="bg-black border-bottom border-secondary py-3 px-4 d-flex justify-content-between align-items-center gap-3">
        <div class="d-flex align-items-center gap-3">
          <img src="/weiß.png" alt="SIA Logo" class="mobile-logo" />
          <div class="mobile-brand">
            <div class="fw-bold">SIA Bier Pong</div>
            <div class="text-secondary small">{{ tournament?.name }}</div>
          </div>
        </div>
        <span class="badge flex-shrink-0" :class="wsConnected ? 'bg-success' : 'bg-secondary'">
          {{ wsConnected ? '● Live' : '○ Offline' }}
        </span>
      </div>

      <!-- Tab Switcher -->
      <div class="d-flex justify-content-center gap-2 bg-dark border-bottom border-secondary py-2">
        <button class="btn btn-sm"
                :class="currentTab === 'groups' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'groups'">Tabellen</button>
        <button class="btn btn-sm"
                :class="currentTab === 'live' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'live'">Live Spiele</button>
        <button class="btn btn-sm"
                :class="currentTab === 'top' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'top'">Top-Spieler</button>
        <button class="btn btn-sm"
                :class="currentTab === 'next' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'next'">Nächste Spiele</button>
        <button class="btn btn-sm"
                :class="currentTab === 'ko' ? 'btn-danger' : 'btn-outline-secondary'"
                @click="currentTab = 'ko'">🏆 KO</button>
      </div>

      <!-- All tabs except KO live inside the container for normal padding/max-width -->
      <div v-if="currentTab !== 'ko'" class="container py-4">

        <!-- Tabellen -->
        <div v-if="currentTab === 'groups'" class="mb-5">
          <h5 class="mb-3 border-bottom border-secondary pb-2">Gruppenphase</h5>
          <div v-if="Object.keys(groupStandings).length" class="row g-3">
            <div v-for="(rows, gname) in groupStandings" :key="gname" class="col-sm-6 col-lg-4">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-header bg-dark border-secondary fw-semibold">{{ gname }}</div>
                <GroupStandingsTable
                  :rows="rows"
                  :active-teams="activeTeamNames"
                  compact
                  max-name-width="160px"
                  empty-text="Keine Daten"
                />
              </div>
            </div>
          </div>
          <div v-else class="text-secondary">Keine Gruppenstände vorhanden.</div>
        </div>

        <!-- Live Spiele -->
        <div v-else-if="currentTab === 'live'" class="mb-5">
          <h5 class="mb-3 border-bottom border-secondary pb-2">Live Spiele</h5>
          <div v-if="activeMatches.length" class="d-flex flex-column gap-4">
            <div v-for="(m, idx) in activeMatches" :key="m.id ?? `${m.group_name}-${idx}`"
                 class="card bg-dark border-secondary text-light overflow-hidden live-match-card">
              <div class="card-body px-3 py-4">
                <LiveTable3D
                  :match="m"
                  :cups-per-game="m.match_cups_per_game ?? cupsPerGame"
                  :table-label="`Tisch ${m.table_no || idx + 1} • ${m.group_name || 'Gruppenphase'}`"
                  compact
                  show-score
                />
              </div>
            </div>
          </div>
          <div v-else class="text-secondary">Aktuell sind keine Live-Spiele aktiv.</div>
        </div>

        <!-- Top-Spieler -->
        <div v-else-if="currentTab === 'top'" class="mb-5">
          <h5 class="mb-3 border-bottom border-secondary pb-2">Top-Spieler (Becher)</h5>
          <div v-if="topPlayers.length" class="list-group">
            <div v-for="(p, idx) in topPlayers" :key="p.label"
                 class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
              <span><strong>{{ idx + 1 }}.</strong> {{ p.label }}</span>
              <span class="text-success fw-bold">{{ p.cups }} Becher</span>
            </div>
          </div>
          <div v-else class="text-secondary">
            Keine Spieler-Statistiken verfügbar. (Spieler-Becherzahlen werden derzeit nicht erfasst.)
          </div>
        </div>

        <!-- Nächste Spiele -->
        <div v-else-if="currentTab === 'next'" class="mb-5">
          <div class="mb-3 border-bottom border-secondary pb-2 d-flex justify-content-between align-items-center gap-2">
            <h5 class="mb-0">Nächste Spiele</h5>
            <span class="badge bg-secondary">{{ upcomingMatches.length }}/{{ upcomingMatchesTotal }}</span>
          </div>
          <div v-if="upcomingMatches.length">
            <div v-for="(m, idx) in upcomingMatches" :key="idx"
                 class="card border-secondary p-3 mb-2 next-match-card text-light">
              <div class="d-flex align-items-center gap-2 flex-wrap mb-2">
                <span class="badge" :class="phaseBadgeClass">{{ phaseLabel }}</span>
                <span class="badge bg-secondary">{{ m.group_name || m.round || '—' }}</span>
                <span class="small text-secondary ms-auto">Match {{ idx + 1 }}</span>
              </div>
              <div class="d-flex align-items-center justify-content-between gap-2">
                <span class="fw-semibold text-white next-team">{{ m.team1 }}</span>
                <span class="text-secondary flex-shrink-0">vs</span>
                <span class="fw-semibold text-white text-end next-team">{{ m.team2 }}</span>
              </div>
            </div>
          </div>
          <div v-else class="text-secondary">Keine anstehenden Spiele.</div>
        </div>

      </div>

      <!-- KO tab: full viewport width (no container) so horizontal scroll works cleanly -->
      <div v-if="currentTab === 'ko'" class="ko-tab-root pt-2 pb-3 px-2">
        <div class="mb-2 px-1 border-bottom border-secondary pb-1" style="font-size:0.8rem;font-weight:700;color:#f8f9fa;">🏆 K.O.-Phase</div>

        <!-- Actual bracket with results — symmetric tree layout -->
        <div v-if="koRounds.length" class="ko-bracket-wrap">
          <KnockoutResultsTree
            :rounds="koRounds"
            :active-match-ids="activeKoMatchIds"
          />
        </div>

        <!-- Preview: seeding placeholders before KO starts -->
        <div v-else-if="koPreviewSlots.length">
          <p class="text-secondary small mb-3 px-2">
            Die K.O.-Phase wurde noch nicht gestartet. Hier siehst du die voraussichtliche Setzliste.
          </p>
          <div class="ko-preview-wrap">
            <KnockoutPreviewTree
              :slots="koPreviewSlots"
              :ko-size="koPreviewSize"
            />
          </div>
        </div>

        <div v-else class="px-2 text-secondary">
          K.O.-Phase noch nicht verfügbar.
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api.js'
import { useTournamentStore } from '../stores/tournament.js'
import LiveTable3D from '../components/LiveTable3D.vue'
import GroupStandingsTable from '../components/GroupStandingsTable.vue'
import {
  DEFAULT_UPCOMING_MATCH_LIMIT,
  getAssignedActiveMatches,
  getUpcomingMatches,
  getUpcomingMatchesTotal,
  getKOActiveMatches,
  getKOUpcomingMatches,
  getKOUpcomingMatchesTotal,
  makeCupsStateFromCount,
} from '../utils/tableAssignments.js'
import KnockoutResultsTree from '../components/KnockoutResultsTree.vue'
import KnockoutPreviewTree from '../components/KnockoutPreviewTree.vue'
import { inferKoMatchCupsTarget, normalizeKoRoundsForDisplay } from '../utils/koDisplay.js'

const route = useRoute()
const store = useTournamentStore()

const loading = ref(true)
const valid   = ref(false)
const token   = computed(() => route.query.token || route.query.mobile_token || '')

const tournament     = computed(() => store.tournament)
const groupStandings = computed(() => {
  const pick = (obj, keys, fallback = 0) => {
    for (const k of keys) {
      if (obj?.[k] !== undefined && obj?.[k] !== null) return obj[k]
    }
    return fallback
  }

  const out = {}
  Object.entries(store.groupStandings || {}).forEach(([groupName, rows]) => {
    out[groupName] = (rows || []).map(row => {
      const wins = Number(pick(row, ['wins', 'win', 'games_won', 'w'], 0)) || 0
      const losses = Number(pick(row, ['losses', 'loss', 'games_lost', 'l'], 0)) || 0
      const cupsFor = Number(pick(row, ['cupsFor', 'cups_for', 'cupsPlus', 'cups_plus', 'cups'], 0)) || 0
      const cupsAgainst = Number(pick(row, ['cupsAgainst', 'cups_against', 'cupsMinus', 'cups_minus'], 0)) || 0
      const cupsDiffRaw = pick(row, ['cupsDiff', 'cups_diff'], null)
      const cupsDiff = Number.isFinite(+cupsDiffRaw) ? +cupsDiffRaw : cupsFor - cupsAgainst
      const pointsRaw = pick(row, ['points', 'pts', 'score'], null)
      const points = Number.isFinite(+pointsRaw) && +pointsRaw > 0 ? +pointsRaw : wins * 2

      return {
        name: pick(row, ['name', 'team', 'team_name', 'teamName'], ''),
        points,
        wins,
        losses,
        cupsFor,
        cupsAgainst,
        cupsDiff,
      }
    })
  })
  return out
})
const koRounds       = computed(() => normalizeKoRoundsForDisplay(store.koPhase?.rounds ?? []))
const wsConnected    = computed(() => store.wsConnected)
const currentPhase   = computed(() => store.tournament?.current_phase ?? store.tournament?.currentPhase ?? store.tournament?.status ?? 'group')
const currentTab     = ref((currentPhase.value === 'ko' || currentPhase.value === 'ko_preview') ? 'ko' : 'groups')
let mobileRefreshTimer = null
const isKnockoutPhase = computed(() => currentPhase.value === 'ko' || currentPhase.value === 'ko_preview')

// Auto-switch to KO tab when admin transitions the tournament to KO phase or preview
watch(currentPhase, (phase) => {
  if (phase === 'ko' || phase === 'ko_preview') currentTab.value = 'ko'
})

// ── KO Preview: placeholder seedings when bracket not yet started ──────────
function normalizeGroupLabel(groupName) {
  const raw = String(groupName ?? '').trim()
  if (!raw) return 'Gruppe'
  return /^gruppe\b/i.test(raw) ? raw : `Gruppe ${raw}`
}

const koPreviewSlots = computed(() => {
  // Rounds already populated — preview not needed
  if (koRounds.value.length > 0) return []

  // Prefer explicit persisted preview slots
  const persistedPreviewSlots = store.koPreview?.slots
  if (Array.isArray(persistedPreviewSlots) && persistedPreviewSlots.length > 0) {
    return persistedPreviewSlots
  }

  // Fall back to play-in-derived slots
  const fromPlayin = store.playin?.direct_qualified_slots
  if (Array.isArray(fromPlayin) && fromPlayin.length > 0) {
    const playinMatches = store.playin?.playin_matches ?? []
    return [
      ...fromPlayin,
      ...playinMatches.map((m, idx) => ({
        id: `playin-mobile-${idx}`,
        sourceLabel: `Sieger Play-In ${idx + 1}`,
        teamName: m?.winner || '',
      })),
    ]
  }

  // Fall back to building from groupStandings
  const tables = store.groupStandings ?? {}
  const winners = []
  const runnersUp = []
  for (const [groupName, rows] of Object.entries(tables)) {
    const label = normalizeGroupLabel(groupName)
    if (rows?.[0]?.name) {
      winners.push({ id: `g-${groupName}-1`, sourceLabel: `Sieger ${label}`, teamName: rows[0].name })
    }
    if (rows?.[1]?.name) {
      runnersUp.push({ id: `g-${groupName}-2`, sourceLabel: `2. ${label}`, teamName: rows[1].name })
    }
  }
  const slots = []
  for (let i = 0; i < winners.length; i++) {
    slots.push(winners[i])
    const runner = runnersUp[runnersUp.length - 1 - i]
    if (runner) slots.push(runner)
  }
  // Append play-in winner placeholders
  const playinMatches = store.playin?.playin_matches ?? []
  playinMatches.forEach((m, idx) => {
    slots.push({
      id: `playin-mobile-${idx}`,
      sourceLabel: `Sieger Play-In ${idx + 1}`,
      teamName: m?.winner || '',
    })
  })
  return slots
})

const koPreviewSize = computed(() => {
  const fromStore = store.koPreview?.ko_size ?? store.koPreview?.koSize ?? store.playin?.ko_size
  if (fromStore) return fromStore
  const n = koPreviewSlots.value.length
  if (n === 0) return 4
  // Round up to next power of 2
  let p = 1
  while (p < n) p *= 2
  return p
})

const cupsPerGame = computed(() =>
  Number(tournament.value?.cupsPerGame ?? tournament.value?.cups_per_game ?? 6) || 6
)
const finaleWith10Cups = computed(() =>
  !!(tournament.value?.finaleWith10Cups ?? tournament.value?.finale_with_10_cups)
)

const activeTableCount = computed(() => {
  const count = Number(tournament.value?.tableCount ?? tournament.value?.table_count ?? 2)
  return Number.isFinite(count) && count > 0 ? count : 2
})
const activeKoMainRoundIndex = computed(() =>
  store.koPhase?.active_main_round_index ?? store.koPhase?.activeMainRoundIndex ?? null
)
const activeKoStageKind = computed(() =>
  store.koPhase?.active_stage_kind ?? store.koPhase?.activeStageKind ?? null
)

const activeKOMatches = computed(() =>
  getKOActiveMatches(koRounds.value, activeTableCount.value, activeKoMainRoundIndex.value, activeKoStageKind.value)
)

function normalizeKoLiveState(rawState, cupsTarget, hitsTaken = 0, isOvertime = false) {
  if (Array.isArray(rawState) && rawState.length === cupsTarget) {
    return [...rawState]
  }
  if (isOvertime && Array.isArray(rawState) && rawState.length === 3 && cupsTarget > 3) {
    const expanded = Array(cupsTarget).fill(false)
    const indices = cupsTarget >= 10 ? [9, 7, 8] : [5, 3, 4]
    indices.forEach((targetIdx, idx) => {
      if (targetIdx < cupsTarget) expanded[targetIdx] = !!rawState[idx]
    })
    return expanded
  }
  return makeCupsStateFromCount(hitsTaken, cupsTarget)
}

const activeKoMatchIds = computed(() =>
  new Set(activeKOMatches.value.map(match => match.id).filter(id => id != null))
)

const activeMatches = computed(() => {
  if (currentPhase.value === 'ko') {
    return activeKOMatches.value.map(m => ({
      ...m,
      group_name: m.round_name || 'KO-Phase',
      ...(() => {
        const cupsTarget = inferKoMatchCupsTarget(m, koRounds.value, cupsPerGame.value, finaleWith10Cups.value)
        return {
          match_cups_per_game: cupsTarget,
          cups_state_team1: normalizeKoLiveState(m.cups_state_team1, cupsTarget, m.cups_team2, !!m.is_overtime),
          cups_state_team2: normalizeKoLiveState(m.cups_state_team2, cupsTarget, m.cups_team1, !!m.is_overtime),
        }
      })(),
    }))
  }
  return getAssignedActiveMatches(store.groupPhase?.matches ?? {}, activeTableCount.value)
})

const activeTeamNames = computed(() => {
  const teams = new Set()
  for (const match of activeMatches.value) {
    if (match.team1) teams.add(match.team1)
    if (match.team2) teams.add(match.team2)
  }
  return Array.from(teams)
})

const upcomingMatches = computed(() =>
  isKnockoutPhase.value
    ? getKOUpcomingMatches(koRounds.value, activeTableCount.value, DEFAULT_UPCOMING_MATCH_LIMIT, activeKoMainRoundIndex.value, activeKoStageKind.value).map(m => ({
        ...m,
        round: m.round_name || 'KO-Phase',
      }))
    : getUpcomingMatches(store.groupPhase?.matches ?? {}, activeTableCount.value, DEFAULT_UPCOMING_MATCH_LIMIT)
)
const upcomingMatchesTotal = computed(() =>
  isKnockoutPhase.value
    ? getKOUpcomingMatchesTotal(koRounds.value, activeTableCount.value, activeKoMainRoundIndex.value, activeKoStageKind.value)
    : getUpcomingMatchesTotal(store.groupPhase?.matches ?? {}, activeTableCount.value)
)

const topPlayers = computed(() => {
  return (store.topPlayers || []).map(p => ({
    label: p.name,
    cups: p.hits
  }))
})

const phaseLabel = computed(() => {
  const phase = currentPhase.value
  if (phase === 'ko') return 'K.O.'
  if (phase === 'ko_preview') return 'KO-Vorschau'
  if (phase === 'playin') return 'Play-In'
  return 'Gruppenphase'
})
const phaseBadgeClass = computed(() => {
  const phase = currentPhase.value
  if (phase === 'ko') return 'bg-danger'
  if (phase === 'ko_preview') return 'bg-warning text-dark'
  if (phase === 'playin') return 'bg-warning text-dark'
  return 'bg-primary'
})

onMounted(async () => {
  if (!token.value) { loading.value = false; return }
  try {
    // Try to find tournament by browsing the state via mobile endpoint
    // We need tournament_id — it comes from the QR URL or we try all
    const tournamentId = route.query.id || route.query.tournament_id
    if (tournamentId) {
      const applyMobileState = data => store.applyState(data)

      const data = await api.tournaments.mobileState(tournamentId, token.value)
      if (!data.error) {
        applyMobileState(data)
        valid.value = true
        store.connectMobile(tournamentId, token.value)
        mobileRefreshTimer = window.setInterval(async () => {
          try {
            const next = await api.tournaments.mobileState(tournamentId, token.value)
            if (!next?.error) {
              applyMobileState(next)
              return
            }
            valid.value = false
            if (mobileRefreshTimer) {
              window.clearInterval(mobileRefreshTimer)
              mobileRefreshTimer = null
            }
          } catch {
            // ignore polling errors; websocket remains primary live path
          }
        }, 5000)
      } else {
        valid.value = false
      }
    } else {
      valid.value = false
    }
  } catch { valid.value = false }
  finally { loading.value = false }
})

onUnmounted(() => {
  if (mobileRefreshTimer) {
    window.clearInterval(mobileRefreshTimer)
    mobileRefreshTimer = null
  }
  store.disconnect()
})
</script>

<style scoped>
.next-match-card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.96) 0%, rgba(10, 10, 10, 0.98) 100%);
}

.next-team {
  min-width: 0;
  flex: 1 1 0;
  word-break: break-word;
}

.live-match-card {
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.96) 0%, rgba(8, 8, 8, 0.98) 100%);
}

.mobile-logo {
  width: 34px;
  height: 34px;
  object-fit: contain;
}

.mobile-brand {
  min-width: 0;
}

.mobile-brand > div {
  max-width: 52vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── KO tab: full width, horizontal scroll enabled ─────────────────────── */
.ko-tab-root {
  width: 100%;
  /* do NOT set overflow:hidden here — let the children scroll */
}

/* ko-bracket-wrap: result tree handles its own horizontal scroll; keep parents open */
.ko-bracket-wrap {
  width: 100%;
  overflow: visible;
}

.ko-bracket-wrap :deep(.bracket-tree),
.ko-preview-wrap :deep(.bracket-tree) {
  --bracket-side-width:   130px !important;
  --bracket-center-width: 150px !important;
  --bracket-gap:          0.45rem !important;
  --bracket-padding:      0.5rem !important;
  --bracket-slot-padding: 0.3rem 0.4rem !important;
}

.ko-bracket-wrap :deep(.bracket-column__title),
.ko-preview-wrap :deep(.bracket-column__title)  { font-size: 0.62rem; }

.ko-bracket-wrap :deep(.bracket-slot__seed),
.ko-preview-wrap :deep(.bracket-slot__seed)     { font-size: 0.6rem; }

.ko-bracket-wrap :deep(.bracket-slot__team),
.ko-preview-wrap :deep(.bracket-slot__team)     { font-size: 0.58rem; }

.ko-bracket-wrap :deep(.bracket-match__label),
.ko-preview-wrap :deep(.bracket-match__label)   { font-size: 0.58rem; }

.ko-bracket-wrap :deep(.bracket-match__versus),
.ko-preview-wrap :deep(.bracket-match__versus)  { font-size: 0.6rem; }

/* ko-preview-wrap: KnockoutPreviewTree needs explicit scroll + mobile scale */
.ko-preview-wrap {
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 0.75rem;
}
</style>
