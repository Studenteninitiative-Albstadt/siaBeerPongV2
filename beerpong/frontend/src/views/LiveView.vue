<template>
  <div class="liveview-root bg-dark text-light d-flex flex-column"
       :class="activeTournament ? 'liveview-root--active' : ''"
       style="background:radial-gradient(circle at top,#1a1a2e 0%,#0d0d0d 60%,#000 100%)">

    <!-- Header -->
    <header class="liveview-header bg-black border-bottom border-secondary">
      <div class="d-flex align-items-center gap-3 flex-shrink-0">
        <img src="/weiß.png" alt="SIA Logo" class="liveview-logo" />
        <div>
          <div class="fw-bold text-white">BeerPong LiveView</div>
          <div class="liveview-brand-subtitle">SIA Beer Pong Turnier</div>
        </div>
      </div>
      <div v-if="activeTournament" class="liveview-active-title">
        <div class="liveview-active-title__name">{{ activeTournament.name }}</div>
        <div class="liveview-active-title__phase">
          Phase: {{ activeTournament.currentPhase ?? activeTournament.current_phase }}
        </div>
      </div>
      <div class="d-flex align-items-center gap-3 flex-shrink-0 ms-auto">
        <span class="badge" :class="wsConnected ? 'bg-success' : 'bg-secondary'">
          {{ wsConnected ? '● Live' : '○ Offline' }}
        </span>
        <button class="btn btn-sm btn-outline-secondary" @click="handleLogout">Abmelden</button>
      </div>
    </header>

    <!-- No active tournament -->
    <div v-if="!activeTournament" class="flex-grow-1 p-4 p-lg-5 liveview-landing">
      <div class="container-fluid">
        <section class="liveview-hero card border-secondary overflow-hidden mb-4">
          <div class="card-body p-4 p-lg-5">
            <div class="row align-items-center g-4">
              <div class="col-lg-8">
                <div class="text-uppercase small liveview-kicker mb-2">Willkommen</div>
                <h1 class="display-3 fw-bold text-white mb-3">Willkommen zum SIA Beer Pong Turnier</h1>
                <p class="lead text-light-emphasis mb-4 liveview-hero-copy">Wintersemester 2025/2026</p>
                <div class="d-flex flex-wrap gap-2">
                  <span class="badge rounded-pill liveview-chip">Gruppenphase</span>
                  <span class="badge rounded-pill liveview-chip">KO-System</span>
                  <span class="badge rounded-pill liveview-chip">Play-In moeglich</span>
                  <span class="badge rounded-pill liveview-chip">Bierkasten fuer Platz 1</span>
                </div>
              </div>
              <div class="col-lg-4">
                <div class="liveview-hero-side card bg-black border-secondary shadow-lg">
                  <div class="card-body">
                    <div class="small text-secondary mb-2">Heute auf dem Beamer</div>
                    <div class="fs-4 fw-bold text-white mb-3">Turnierhalle, TL;DR und Upcoming Events</div>
                    <div class="small text-light-emphasis">
                      Die Inhalte dieser Startansicht uebernehmen jetzt die bestehende Admin-Landing-Page,
                      bleiben aber im beamerfreundlichen LiveView-Layout.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div class="row g-4">
          <div class="col-xl-4 col-lg-5">
            <div class="card bg-black border-secondary h-100 shadow-lg">
              <div class="card-header border-secondary bg-black">
                <strong>TL;DR</strong>
              </div>
              <div class="card-body">
                <div class="d-flex flex-column gap-3">
                  <div v-for="rule in liveviewRules" :key="rule.title" class="liveview-rule">
                    <div class="fw-semibold text-white mb-1">{{ rule.title }}</div>
                    <div v-if="rule.text" class="small text-secondary">{{ rule.text }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-xl-4 col-lg-7">
            <div class="card bg-black border-secondary h-100 shadow-lg">
              <div class="card-header border-secondary bg-black">
                <strong>Upcoming Events</strong>
              </div>
              <div class="card-body">
                <div class="d-flex flex-column gap-3">
                  <div v-for="event in liveviewEvents" :key="event.time + event.title" class="liveview-event">
                    <div class="d-flex align-items-start gap-3">
                      <div class="liveview-event-time">{{ event.time }}</div>
                      <div>
                        <div class="fw-semibold text-white">{{ event.title }}</div>
                        <div class="small text-secondary">{{ event.text }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-xl-4">
            <div class="card bg-black border-secondary h-100 shadow-lg">
              <div class="card-header border-secondary bg-black d-flex justify-content-between align-items-center">
                <strong>Turnier auswaehlen</strong>
                <span class="small text-secondary">{{ store.tournaments.length }} verfuegbar</span>
              </div>
              <div class="card-body">
                <div v-if="store.tournaments.length === 0" class="text-secondary small">
                  Keine Turniere vorhanden.
                </div>
                <div v-else class="list-group liveview-tournament-list">
                  <button v-for="t in store.tournaments" :key="t.id"
                          class="list-group-item list-group-item-action bg-dark text-light border-secondary"
                          @click="selectTournament(t)">
                    <div class="fw-bold">{{ t.name }}</div>
                    <small class="text-secondary">Phase: {{ t.current_phase ?? t.currentPhase ?? '–' }}</small>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active tournament -->
    <template v-else>

      <!-- K.O.-Phase / Vorschau: Full-screen bracket view -->
      <LiveViewKO v-if="isKoFullscreen" @deselect="deselectTournament" />

      <!-- Group / Play-In: normal live layout -->
      <div v-else class="lv-shell">

        <!-- ── Zeile 1: Live-Tische (links) + Nächste Spiele (rechts) ── -->
        <div class="lv-row-top">

          <div class="lv-tables-col">
            <div class="lv-label">🔴 Live Spiele</div>
            <div v-if="activeMatches.length" class="lv-tables-scroll">
              <LiveTable3D
                v-for="(m, i) in activeMatches" :key="m.id"
                :match="m"
                :cups-per-game="Number(activeTournament?.cupsPerGame ?? activeTournament?.cups_per_game ?? 6)"
                :team1-players="formatPlayers(m.team1)"
                :team2-players="formatPlayers(m.team2)"
                :table-label="`Tisch ${m.table_no || i + 1} • ${m.group_name}`"
                beam show-score
              />
            </div>
            <div v-else class="lv-no-games">
              <span class="text-secondary">Keine aktiven Spiele</span>
            </div>
          </div>

          <div class="lv-queue-col">
            <div class="card bg-black border-secondary lv-queue-card">
              <div class="card-header bg-black border-secondary d-flex justify-content-between align-items-center">
                <strong>Nächste Spiele</strong>
                <span class="badge bg-secondary">{{ upcomingMatches.length }}</span>
              </div>
              <div class="card-body p-0 overflow-auto">
                <div v-if="upcomingMatches.length" class="list-group list-group-flush">
                  <div v-for="(m, idx) in upcomingMatches"
                       :key="m.id ?? `${m.group_name}-${idx}`"
                       class="list-group-item bg-transparent text-light border-secondary-subtle lv-queue-item">
                    <div class="d-flex align-items-center justify-content-between gap-1 mb-1">
                      <span class="badge bg-secondary lv-queue-badge">{{ m.group_name }}</span>
                      <span class="text-secondary lv-queue-num">#{{ idx + 1 }}</span>
                    </div>
                    <div class="fw-semibold text-white lv-queue-team">{{ m.team1 }}</div>
                    <div class="text-secondary lv-queue-vs">vs</div>
                    <div class="fw-semibold text-white lv-queue-team">{{ m.team2 }}</div>
                  </div>
                </div>
                <div v-else class="p-3 text-secondary small">Keine weiteren Spiele.</div>
              </div>
            </div>
          </div>

        </div>

        <!-- ── Zeile 2: Gruppenstaende (links) + QR-Code (rechts) ── -->
        <div class="lv-row-bottom">

          <div class="lv-standings-col">
            <div v-if="groupCount > 0" class="live-carousel-container">
              <div class="carousel-viewport">
                <div class="carousel-track"
                     :style="{ transform: `translateX(calc(-${carouselIndex * 80}% + 10%))` }">
                  <div v-for="(g, idx) in groupEntries" :key="g.name"
                       class="carousel-slide"
                       :class="{ 'is-active': carouselIndex === idx, 'is-ghost': carouselIndex !== idx }"
                       @click="setCarousel(idx)">
                    <div class="card bg-dark border-secondary h-100 carousel-card">
                      <div class="card-header bg-dark border-secondary d-flex justify-content-between align-items-center">
                        <span class="fw-semibold text-white">{{ g.name }}</span>
                        <div v-if="carouselIndex === idx && groupCount > 1" class="btn-group btn-group-sm">
                          <button class="btn btn-outline-secondary" @click.stop="goPrevGroup">‹</button>
                          <button class="btn btn-outline-secondary" @click.stop="goNextGroup">›</button>
                        </div>
                      </div>
                      <div class="card-body p-0">
                        <GroupStandingsTable
                          :rows="g.rows"
                          :active-teams="activeTeamNames"
                          compact
                          max-name-width="140px"
                          empty-text="Keine Daten"
                        />
                      </div>
                      <div v-if="groupCount > 1" class="card-footer bg-dark border-secondary text-center py-1">
                        <div class="d-flex justify-content-center gap-2">
                          <button v-for="(dot, i) in groupEntries" :key="dot.name"
                                  class="btn btn-sm dot-btn"
                                  :class="i === carouselIndex ? 'btn-primary' : 'btn-outline-secondary'"
                                  @click.stop="setCarousel(i)"
                                  :title="dot.name"></button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="card bg-dark border-secondary p-3 text-center text-secondary small">
              Keine Gruppenstaende verfuegbar
            </div>
          </div>

          <div class="lv-qr-col">
            <div class="card bg-black border-secondary h-100 text-center p-3">
              <h6 class="text-secondary mb-2 small">Mobile Ansicht</h6>
              <canvas ref="qrCanvas" class="mx-auto d-block liveview-qr"></canvas>
              <div class="mt-1">
                <small class="text-secondary d-block liveview-qr-url">{{ mobileUrl }}</small>
              </div>
            </div>
          </div>

        </div>

        <!-- KO-Phase -->
        <div v-if="koRounds.length" class="lv-ko-block">
          <div class="lv-label mb-1">K.O.-Phase</div>
          <div v-for="round in koRounds" :key="round.round_name" class="mb-2">
            <div class="fw-semibold text-white mb-1 small">{{ round.round_name }}</div>
            <div class="d-flex flex-wrap gap-2">
              <div v-for="(m, idx) in round.matches" :key="idx"
                   class="card bg-dark border-secondary px-3 py-2 text-light small">
                <div class="d-flex align-items-center gap-2">
                  <span :class="m.winner === m.team1 ? 'fw-bold text-success' : ''">{{ m.team1 || '?' }}</span>
                  <span class="text-secondary">vs</span>
                  <span :class="m.winner === m.team2 ? 'fw-bold text-success' : ''">{{ m.team2 || '?' }}</span>
                </div>
                <div v-if="m.winner" class="text-success mt-1 small">🏆 {{ m.winner }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="border-top border-secondary py-2 px-3 text-center lv-footer">
          <button class="btn btn-outline-secondary btn-sm" @click="deselectTournament">Anderes Turnier</button>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import QRCode from 'qrcode'
import { useAuthStore } from '../stores/auth.js'
import { useTournamentStore } from '../stores/tournament.js'
import LiveTable3D from '../components/LiveTable3D.vue'
import GroupStandingsTable from '../components/GroupStandingsTable.vue'
import { getAssignedActiveMatches, getUpcomingMatches } from '../utils/tableAssignments.js'
import LiveViewKO from '../components/LiveViewKO.vue'
import { normalizeKoRoundsForDisplay } from '../utils/koDisplay.js'

const auth   = useAuthStore()
const store  = useTournamentStore()
const router = useRouter()

const CAROUSEL_MS = 6000
const activeTournament = computed(() => store.tournament)
const currentPhase     = computed(() =>
  activeTournament.value?.current_phase ?? activeTournament.value?.currentPhase ?? 'group'
)
const isKoFullscreen = computed(() =>
  currentPhase.value === 'ko' || currentPhase.value === 'ko_preview'
)
const qrCanvas = ref(null)
const carouselIndex = ref(0)
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1920)
const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 1080)
let carouselTimer = null

const liveviewRules = [
  {
    title: 'Gespielt wird in Gruppenphase -> KO-System.',
    text: '',
  },
  {
    title: 'Pro Spiel: 2 x 0,33 l Bier',
    text: '(an der Bar fuer 2,50 EUR).',
  },
  {
    title: 'Je nach Teilnehmeranzahl kann es ein Play-In fuer die KO-Phase geben.',
    text: '',
  },
  {
    title: 'Gewertet werden Siege/Niederlagen und getroffene/kassierte Becher.',
    text: '',
  },
  {
    title: 'Der Sieger des Turniers gewinnt einen Bierkasten.',
    text: '',
  },
]

const liveviewEvents = [
  {
    time: '18.11.2025',
    title: 'Just Open',
    text: '20:00 · Plan B',
  },
  {
    time: '20.11.2025',
    title: 'Blacklight',
    text: '20:00 · Plan B',
  },
  {
    time: '21.11.2025',
    title: 'Mental Health Coffee Break',
    text: '14:00 · Plan B',
  },
]

const wsConnected = computed(() => store.wsConnected)
const koRounds    = computed(() => normalizeKoRoundsForDisplay(store.koPhase?.rounds ?? []))

const groupStandings = computed(() => {
  const pick = (obj, keys, fallback = 0) => {
    for (const k of keys) {
      if (obj?.[k] !== undefined && obj?.[k] !== null) return obj[k]
    }
    return fallback
  }
  const out = {}
  Object.entries(store.groupStandings || {}).forEach(([g, rows]) => {
    out[g] = (rows || []).map(r => {
      const wins        = Number(pick(r, ['wins', 'win', 'games_won', 'w'], 0)) || 0
      const losses      = Number(pick(r, ['losses', 'loss', 'games_lost', 'l'], 0)) || 0
      const cupsFor     = Number(pick(r, ['cupsFor', 'cups_for', 'cupsPlus', 'cups_plus', 'cups'], 0)) || 0
      const cupsAgainst = Number(pick(r, ['cupsAgainst', 'cups_against', 'cupsMinus', 'cups_minus'], 0)) || 0
      const cupsDiffRaw = pick(r, ['cupsDiff', 'cups_diff'], null)
      const cupsDiff    = Number.isFinite(+cupsDiffRaw) ? +cupsDiffRaw : cupsFor - cupsAgainst
      const pointsRaw   = pick(r, ['points', 'pts', 'score'], null)
      const points      = Number.isFinite(+pointsRaw) && +pointsRaw > 0 ? +pointsRaw : wins * 2
      return {
        name: pick(r, ['name', 'team', 'team_name', 'teamName'], ''),
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

/* Logik für die Aktiven Live Tische (identisch zu GroupsView) */
const activeMatches = computed(() =>
  getAssignedActiveMatches(
    store.groupPhase?.matches || {},
    activeTournament.value?.tableCount ?? activeTournament.value?.table_count ?? 2
  )
)

const activeTeamNames = computed(() => {
  const teams = new Set()
  for (const match of activeMatches.value) {
    if (match.team1) teams.add(match.team1)
    if (match.team2) teams.add(match.team2)
  }
  return Array.from(teams)
})

const upcomingMatches = computed(() =>
  getUpcomingMatches(
    store.groupPhase?.matches || {},
    activeTournament.value?.tableCount ?? activeTournament.value?.table_count ?? 2,
    6
  )
)

const groupEntries = computed(() =>
  Object.entries(groupStandings.value || {}).map(([name, rows]) => ({
    name,
    rows
  }))
)
const groupCount = computed(() => groupEntries.value.length)

const mobileUrl = computed(() => {
  if (!activeTournament.value?.mobileAccessToken || !activeTournament.value?.id) return ''
  const base = window.location.origin + window.location.pathname
  return `${base}#/mobile?token=${activeTournament.value.mobileAccessToken}&id=${activeTournament.value.id}`
})

const qrCodeSize = computed(() => {
  const byWidth = viewportWidth.value * 0.13
  const byHeight = viewportHeight.value * 0.18
  return Math.round(Math.max(120, Math.min(240, byWidth, byHeight)))
})

onMounted(async () => {
  await store.fetchList()
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  store.disconnect()
  stopCarousel()
  window.removeEventListener('resize', handleResize)
})

watch(mobileUrl, async (url) => {
  if (!url || !qrCanvas.value) return
  await nextTick()
  try {
    await QRCode.toCanvas(qrCanvas.value, url, { width: qrCodeSize.value, color: { dark: '#ffffff', light: '#000000' } })
  } catch (e) { console.error('QR error', e) }
})

watch(qrCodeSize, async () => {
  if (!mobileUrl.value || !qrCanvas.value) return
  await nextTick()
  try {
    await QRCode.toCanvas(qrCanvas.value, mobileUrl.value, { width: qrCodeSize.value, color: { dark: '#ffffff', light: '#000000' } })
  } catch (e) { console.error('QR resize error', e) }
})

async function selectTournament(t) {
  await store.load(t.id)
  store.connect(t.id)
  carouselIndex.value = 0
  stopCarousel()
  startCarousel()
  // render QR
  await nextTick()
  if (qrCanvas.value && mobileUrl.value) {
    QRCode.toCanvas(qrCanvas.value, mobileUrl.value, { width: qrCodeSize.value, color: { dark: '#ffffff', light: '#000000' } }).catch(() => {})
  }
}

function deselectTournament() {
  store.tournament = null
  store.disconnect()
  stopCarousel()
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function resetCarousel() {
  stopCarousel()
  startCarousel()
}

function stopCarousel() {
  if (carouselTimer) {
    clearInterval(carouselTimer)
    carouselTimer = null
  }
}

function handleResize() {
  viewportWidth.value = window.innerWidth
  viewportHeight.value = window.innerHeight
}

function startCarousel() {
  if (groupCount.value > 1) {
    carouselTimer = setInterval(() => {
      carouselIndex.value = (carouselIndex.value + 1) % groupCount.value
    }, CAROUSEL_MS)
  }
}

function setCarousel(i) {
  carouselIndex.value = i
  stopCarousel()
  startCarousel()
}
function goNextGroup() {
  if (groupCount.value === 0) return
  carouselIndex.value = (carouselIndex.value + 1 + groupCount.value) % groupCount.value
  stopCarousel()
  startCarousel()
}
function goPrevGroup() {
  if (groupCount.value === 0) return
  carouselIndex.value =
    (carouselIndex.value - 1 + groupCount.value) % groupCount.value
  stopCarousel()
  startCarousel()
}

function formatPlayers(teamName) {
  const p = store.teamPlayers?.[teamName]
  if (!p) return ''
  if (p.player1 && p.player2) return `${p.player1} & ${p.player2}`
  return p.player1 || p.player2 || ''
}

watch(groupEntries, () => {
  if (groupCount.value === 0) {
    carouselIndex.value = 0
    stopCarousel()
  } else {
    carouselIndex.value = carouselIndex.value % groupCount.value
    stopCarousel()
    startCarousel()
  }
}, { deep: true })
</script>

<style scoped>
.liveview-root {
  min-height: 100dvh;
}

/* Locked viewport when a tournament is active */
.liveview-root--active {
  height: 100dvh;
  overflow: hidden;
}

/* ── Header: plain flexbox, no Bootstrap navbar conflicts ───────────────── */
.liveview-header {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  min-height: 60px;
}

.liveview-active-title {
  flex: 1 1 0;
  min-width: 0;
  text-align: center;
}

.liveview-active-title__name {
  color: #fff;
  font-size: clamp(1rem, 1.6vw, 1.45rem);
  font-weight: 700;
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.liveview-active-title__phase {
  color: rgba(255, 255, 255, 0.52);
  font-size: clamp(0.68rem, 0.85vw, 0.8rem);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* ── Active tournament – zwei-Zeilen-Layout ─────────────────────────────── */
.lv-shell {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: clamp(8px, 1vh, 14px) clamp(10px, 1.2vw, 18px);
  gap: clamp(6px, 0.8vh, 10px);
  overflow: hidden;
}

/* Zeile 1: Live-Tische + Nächste-Spiele-Queue */
.lv-row-top {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  gap: clamp(8px, 1vw, 14px);
}

.lv-tables-col {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.lv-tables-scroll {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-wrap: nowrap;
  gap: clamp(15px, 2vw, 32px);
  align-items: center;
  justify-content: center;
  overflow: hidden; /* Prevent any bleed through */
  padding: 10px 0;
}

/* Make tables larger in beam mode inside LiveView (group phase) */
.lv-tables-scroll :deep(.beer-table--beam) {
  /* Strictly tied to available height to prevent overlap */
  --tw:    clamp(120px, min(12vw, 15vh), 210px);
  --ratio: 2.3;
}

.lv-no-games {
  flex: 1 1 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lv-queue-col {
  flex: 0 0 clamp(160px, 15vw, 220px);
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.lv-queue-card {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(4,4,4,0.98) 0%, rgba(14,18,26,0.98) 100%);
  border-color: rgba(255,255,255,0.16) !important;
}

.lv-queue-card :deep(.card-header) {
  flex: 0 0 auto;
  padding: 0.45rem 0.75rem;
}

.lv-queue-card :deep(.card-body) {
  flex: 1 1 0;
  min-height: 0;
}

.lv-queue-item {
  padding: 0.48rem 0.6rem;
  background: rgba(255,255,255,0.04) !important;
  border-bottom-color: rgba(255,255,255,0.08) !important;
}

.lv-queue-badge { font-size: 0.68rem; }
.lv-queue-num   { font-size: 0.68rem; }
.lv-queue-vs    { font-size: 0.7rem; margin: 1px 0; }
.lv-queue-team  { font-size: clamp(0.72rem, 0.85vw, 0.85rem); }

/* Zeile 2: Gruppenstaende + QR-Code */
.lv-row-bottom {
  flex: 0 0 clamp(135px, 25.5vh, 230px);
  min-height: 0;
  display: flex;
  gap: clamp(8px, 1vw, 14px);
  position: relative;
  z-index: 10;
}

.lv-standings-col {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.lv-qr-col {
  flex: 0 0 clamp(160px, 15vw, 220px);
  min-height: 0;
}

.lv-ko-block {
  flex: 0 0 auto;
  max-height: 90px;
  overflow: auto;
}

.lv-footer {
  flex: 0 0 auto;
}

.lv-label {
  flex: 0 0 auto;
  font-size: clamp(0.7rem, 0.88vw, 0.86rem);
  font-weight: 600;
  color: rgba(255,255,255,0.58);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.liveview-section-title {
  font-size: clamp(1rem, 1.4vw, 1.35rem);
}

.liveview-logo {
  width: clamp(34px, 2.3vw, 46px);
  height: clamp(34px, 2.3vw, 46px);
  object-fit: contain;
  filter: drop-shadow(0 4px 10px rgba(255, 255, 255, 0.12));
}

.liveview-brand-subtitle {
  font-size: clamp(0.62rem, 0.85vw, 0.72rem);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.48);
}

.liveview-landing {
  background:
    radial-gradient(circle at 10% 15%, rgba(255, 185, 65, 0.12), transparent 24%),
    radial-gradient(circle at 85% 18%, rgba(88, 166, 255, 0.12), transparent 22%);
}

.liveview-hero {
  background:
    linear-gradient(135deg, rgba(8, 8, 8, 0.96) 0%, rgba(16, 28, 42, 0.96) 58%, rgba(41, 67, 54, 0.94) 100%);
}

.liveview-kicker {
  letter-spacing: 0.18em;
  color: rgba(255, 214, 102, 0.86);
}

.liveview-hero-copy {
  max-width: 48rem;
}

.liveview-chip {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.16);
  padding: 0.55rem 0.85rem;
}

.liveview-rule,
.liveview-event {
  padding: 0.85rem 0.95rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.liveview-event-time {
  min-width: 64px;
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #ffd166 0%, #f4a261 100%);
  color: #201607;
  font-size: 0.78rem;
  font-weight: 700;
  text-align: center;
}

.liveview-tournament-list .list-group-item {
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.liveview-tournament-list .list-group-item:hover {
  background-color: #111723 !important;
  transform: translateY(-1px);
}

.liveview-queue-card {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(4, 4, 4, 0.98) 0%, rgba(14, 18, 26, 0.98) 100%);
  border-color: rgba(255, 255, 255, 0.16) !important;
  overflow: hidden;
}

.liveview-queue-card :deep(.card-header) {
  flex: 0 0 auto;
}

.liveview-queue-card :deep(.card-body) {
  flex: 1 1 0;
  min-height: 0;
  overflow: auto;
}

.liveview-queue-item {
  padding: 0.6rem 0.7rem;
  background: rgba(255, 255, 255, 0.05) !important;
  border-bottom-color: rgba(255, 255, 255, 0.08) !important;
}

.liveview-qr {
  width: 100%;
  max-width: min(22vh, 14vw, 180px);
  aspect-ratio: 1;
}

.liveview-qr-url {
  font-size: 0.38rem;
  word-break: break-all;
  overflow-wrap: anywhere;
  color: rgba(255,255,255,0.22) !important;
  line-height: 1.1;
  display: block;
  max-width: 100%;
}

/* Carousel inside .lv-standings-col */
.live-carousel-container {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.carousel-viewport {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.carousel-track {
  display: flex;
  height: 100%;
  transition: transform 0.5s cubic-bezier(0.25, 1, 0.5, 1);
}

.carousel-slide {
  flex: 0 0 80%;
  padding: 0 8px;
  height: 100%;
  transition: all 0.5s ease;
  cursor: pointer;
}

.carousel-slide.is-ghost {
  opacity: 0.35;
  transform: scale(0.9);
  filter: blur(2px);
}

.carousel-slide.is-active {
  opacity: 1;
  transform: scale(1);
  filter: blur(0);
  z-index: 2;
}

.carousel-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.carousel-card :deep(.card-header) {
  flex: 0 0 auto;
  padding: 0.38rem 0.65rem;
}

.carousel-card :deep(.card-body) {
  flex: 1 1 0;
  min-height: 0;
  overflow: auto;
  padding: 0;
}

.carousel-card :deep(.card-footer) {
  flex: 0 0 auto;
  padding: 0.28rem 0.5rem;
}

.carousel-card :deep(.table) {
  font-size: clamp(0.66rem, 0.88vw, 0.84rem);
}

.carousel-card :deep(th),
.carousel-card :deep(td) {
  padding-top: 0.26rem;
  padding-bottom: 0.26rem;
}

.dot-btn {
  width: 10px;
  height: 10px;
  padding: 0;
  border-radius: 50%;
}

@media (max-height: 800px) {
  .liveview-brand-subtitle { display: none; }

  .liveview-active-title__name  { font-size: clamp(0.88rem, 1.2vw, 1.05rem); }
  .liveview-active-title__phase { font-size: 0.66rem; }

  .lv-row-bottom {
    flex-basis: clamp(160px, 30vh, 270px);
  }

  .carousel-card :deep(.table) { font-size: 0.66rem; }

  .carousel-card :deep(.card-header),
  .lv-queue-card :deep(.card-header) {
    padding: 0.32rem 0.55rem;
  }

  .liveview-qr {
    max-width: min(16vh, 13vw, 150px);
  }
}

@media (max-width: 900px) {
  .liveview-header {
    flex-wrap: wrap;
    gap: 8px 16px;
    padding: 10px 16px;
  }

  /* Tournament title drops below brand + actions on narrow screens */
  .liveview-active-title {
    order: 3;
    flex: 1 0 100%;
    text-align: left !important;
  }

  .liveview-active-title__name {
    white-space: normal;
    overflow: visible;
    text-overflow: unset;
  }

  .lv-queue-col { flex-basis: clamp(130px, 26vw, 180px); }
  .lv-qr-col   { flex-basis: clamp(130px, 26vw, 180px); }
}

@media (max-width: 640px) {
  .liveview-header { padding: 8px 12px; }
  .liveview-logo   { width: 30px; height: 30px; }
}
</style>
