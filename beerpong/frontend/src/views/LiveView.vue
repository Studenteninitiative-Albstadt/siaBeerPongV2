<template>
  <div class="min-vh-100 bg-dark text-light d-flex flex-column"
       style="background:radial-gradient(circle at top,#1a1a2e 0%,#0d0d0d 60%,#000 100%)">

    <!-- Header -->
    <nav class="navbar navbar-dark bg-black border-bottom border-secondary px-4 py-2">
      <span class="navbar-brand fw-bold">🍺 BeerPong LiveView</span>
      <div class="d-flex align-items-center gap-3">
        <span class="badge" :class="wsConnected ? 'bg-success' : 'bg-secondary'">
          {{ wsConnected ? '● Live' : '○ Offline' }}
        </span>
        <button class="btn btn-sm btn-outline-secondary" @click="handleLogout">Abmelden</button>
      </div>
    </nav>

    <!-- No active tournament -->
    <div v-if="!activeTournament" class="flex-grow-1 d-flex flex-column align-items-center justify-content-center gap-3 p-4">
      <h4 class="text-secondary">Turnier auswählen</h4>
      <div v-if="store.tournaments.length === 0" class="text-secondary small">Keine Turniere vorhanden.</div>
      <div v-else class="list-group" style="min-width:340px">
        <button v-for="t in store.tournaments" :key="t.id"
                class="list-group-item list-group-item-action bg-dark text-light border-secondary"
                @click="selectTournament(t)">
          <div class="fw-bold">{{ t.name }}</div>
          <small class="text-secondary">Phase: {{ t.current_phase ?? t.currentPhase ?? '–' }}</small>
        </button>
      </div>
    </div>

    <!-- Active tournament -->
    <template v-else>
      <div class="container-fluid py-4 flex-grow-1">
        
        <!-- ================= 3D LIVE TISCHE ================= -->
        <div v-if="activeMatches.length > 0" class="mb-5">
          <h4 class="text-white mb-4 text-center">🔴 Live Spiele</h4>
          <div class="row g-5 justify-content-center">
            
            <div v-for="(m, i) in activeMatches" :key="m.id" class="col-auto">
              <div class="d-flex flex-column align-items-center">
                <!-- Team 2 (Oben) -->
                <div class="text-center mb-3 z-index-1">
                  <h4 class="text-white mb-0">{{ m.team2 }}</h4>
                  <div class="text-secondary small">{{ formatPlayers(m.team2) }}</div>
                </div>
                
                <!-- Isometrischer Tisch -->
                <div class="iso-table-container">
                  <div class="iso-table shadow-lg">
                    <div class="iso-cup-zone top-zone">
                      <div v-for="(row, rIdx) in buildPyramid(m.cups_state_team2, Number(activeTournament.cupsPerGame) === 10)" :key="'t2-r'+rIdx" class="iso-cup-row">
                        <div v-for="cup in row" :key="'t2-c'+cup.idx" class="iso-cup" :class="{'is-hit': !cup.val}"><div class="cup-inner"></div></div>
                      </div>
                    </div>
                    <div class="iso-net"></div>
                    <div class="iso-cup-zone bottom-zone">
                      <div v-for="(row, rIdx) in buildPyramid(m.cups_state_team1, Number(activeTournament.cupsPerGame) === 10)" :key="'t1-r'+rIdx" class="iso-cup-row">
                        <div v-for="cup in row" :key="'t1-c'+cup.idx" class="iso-cup" :class="{'is-hit': !cup.val}"><div class="cup-inner"></div></div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Team 1 (Unten) -->
                <div class="text-center mt-4 z-index-1">
                  <h4 class="text-white mb-0">{{ m.team1 }}</h4>
                  <div class="text-secondary small">{{ formatPlayers(m.team1) }}</div>
                </div>
                
                <div class="mt-3 badge bg-warning text-dark fs-6 shadow">Tisch {{ i + 1 }} • {{ m.group_name }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="row g-4">

          <!-- QR-Code Bereich -->
          <div class="col-lg-4 col-md-5">
            <div class="card bg-black border-secondary h-100 text-center p-3">
              <h6 class="text-secondary mb-3">Mobile Ansicht</h6>
              <canvas ref="qrCanvas" class="mx-auto d-block" style="max-width:200px;width:100%"></canvas>
              <div class="mt-3">
                <small class="text-secondary d-block">{{ mobileUrl }}</small>
              </div>
            </div>
          </div>

          <!-- Gruppen-Tabellen im Carousel -->
          <div class="col-lg-8 col-md-7">
            <h5 class="mb-3 d-flex align-items-center justify-content-between">
              <span>
                {{ activeTournament.name }}
                <span class="badge bg-secondary ms-2 fs-6">{{ activeTournament.currentPhase ?? activeTournament.current_phase }}</span>
              </span>
              <small class="text-secondary">Auto-Rotation: {{ CAROUSEL_MS / 1000 }}s</small>
            </h5>

            <div class="live-carousel-container mb-3" v-if="groupCount > 0">
              <div class="carousel-viewport">
                <div 
                  class="carousel-track" 
                  :style="{ transform: `translateX(calc(-${carouselIndex * 80}% + 10%))` }"
                >
                  <div 
                    v-for="(g, idx) in groupEntries" 
                    :key="g.name"
                    class="carousel-slide"
                    :class="{ 'is-active': carouselIndex === idx, 'is-ghost': carouselIndex !== idx }"
                    @click="setCarousel(idx)"
                  >
                    <div class="card bg-dark border-secondary h-100 carousel-card shadow-lg">
                      <div class="card-header d-flex justify-content-between align-items-center bg-dark border-secondary">
                        <span class="fw-semibold">{{ g.name }}</span>
                        <div class="btn-group btn-group-sm" role="group" v-if="carouselIndex === idx">
                          <button class="btn btn-outline-secondary" @click.stop="goPrevGroup" :disabled="groupCount === 0">‹</button>
                          <button class="btn btn-outline-secondary" @click.stop="goNextGroup" :disabled="groupCount === 0">›</button>
                        </div>
                      </div>
                      <div class="card-body p-0">
                        <div class="bg-gradient text-start px-3 py-2 border-bottom border-secondary">
                          <small class="text-secondary">Gruppe</small>
                          <div class="fw-semibold text-white fs-6">{{ g.name }}</div>
                        </div>
                        <div class="table-responsive">
                          <table class="table table-dark table-sm mb-0 align-middle">
                            <thead>
                              <tr>
                                <th>#</th>
                                <th>Team</th>
                                <th class="text-center">P</th>
                                <th class="text-center">S</th>
                                <th class="text-center">N</th>
                                <th class="text-center">B+</th>
                                <th class="text-center">B-</th>
                                <th class="text-center">±</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="(r, rIdx) in g.rows" :key="r.name"
                                  :class="rIdx < 2 ? 'table-success' : ''">
                                <td>{{ rIdx + 1 }}</td>
                                <td class="text-truncate" style="max-width: 160px;" :title="r.name">{{ r.name }}</td>
                                <td class="text-center fw-bold">{{ r.points }}</td>
                                <td class="text-center text-success">{{ r.wins }}</td>
                                <td class="text-center text-danger">{{ r.losses }}</td>
                                <td class="text-center">{{ r.cupsFor }}</td>
                                <td class="text-center">{{ r.cupsAgainst }}</td>
                                <td class="text-center" :class="r.cupsDiff > 0 ? 'text-success' : r.cupsDiff < 0 ? 'text-danger' : ''">
                                  {{ r.cupsDiff > 0 ? '+' : '' }}{{ r.cupsDiff }}
                                </td>
                              </tr>
                              <tr v-if="g.rows.length === 0">
                                <td colspan="8" class="text-center text-secondary py-3">Keine Daten</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                      <div v-if="groupCount > 1" class="card-footer mt-auto bg-dark border-secondary text-center">
                        <div class="d-flex justify-content-center gap-2">
                          <button
                            v-for="(dot, i) in groupEntries"
                            :key="dot.name"
                            class="btn btn-sm dot-btn"
                            :class="i === carouselIndex ? 'btn-primary' : 'btn-outline-secondary'"
                            @click.stop="setCarousel(i)"
                            :title="dot.name"
                          ></button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="card bg-dark border-secondary p-4 text-center text-secondary mb-3">
              Keine Gruppenstände verfügbar
            </div>
          </div>
        </div>

        <!-- KO rounds -->
        <div v-if="koRounds.length" class="mb-4">
          <h6 class="text-secondary mb-2">K.O.-Phase</h6>
          <div v-for="round in koRounds" :key="round.round_name" class="mb-3">
            <div class="fw-semibold text-white mb-1">{{ round.round_name }}</div>
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
      </div>

      <div class="border-top border-secondary p-3 text-center">
        <button class="btn btn-outline-secondary btn-sm" @click="deselectTournament">Anderes Turnier</button>
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

const auth   = useAuthStore()
const store  = useTournamentStore()
const router = useRouter()
const API = import.meta.env.VITE_API_BASE || ''

const CAROUSEL_MS = 6000
const activeTournament = ref(null)
const qrCanvas = ref(null)
const carouselIndex = ref(0)
let carouselTimer = null

/* Live Data für die Tische */
const liveGroupMatches = ref({})
const liveTeams = ref([])
let pollingTimer = null

const wsConnected = computed(() => store.wsConnected)
const koRounds    = computed(() => store.koPhase?.rounds ?? [])

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
const activeMatches = computed(() => {
  const arr = []
  for (const [gName, ms] of Object.entries(liveGroupMatches.value)) {
    for (let i = 0; i < ms.length; i++) {
      arr.push({ ...ms[i], group_name: gName, originalIndex: i })
    }
  }
  arr.sort((a, b) => {
    if (a.order_index !== b.order_index) return a.order_index - b.order_index
    return a.group_name.localeCompare(b.group_name, 'de')
  })
  
  const pendingMatches = arr.filter(m => !m.winner)
  const active = []
  const playingTeams = new Set()
  const tCount = activeTournament.value?.tableCount ?? activeTournament.value?.table_count ?? 2

  for (const m of pendingMatches) {
    if (active.length >= tCount) break
    if (!playingTeams.has(m.team1) && !playingTeams.has(m.team2)) {
      active.push(m)
      playingTeams.add(m.team1)
      playingTeams.add(m.team2)
    }
  }
  return active
})

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

onMounted(async () => {
  await store.fetchList()
})

onUnmounted(() => {
  store.disconnect()
  stopCarousel()
  if (pollingTimer) clearInterval(pollingTimer)
})

watch(mobileUrl, async (url) => {
  if (!url || !qrCanvas.value) return
  await nextTick()
  try {
    await QRCode.toCanvas(qrCanvas.value, url, { width: 200, color: { dark: '#ffffff', light: '#000000' } })
  } catch (e) { console.error('QR error', e) }
})

async function fetchLiveTableData() {
  if (!activeTournament.value?.id) return
  try {
    const ts = new Date().getTime()
    const res = await fetch(`${API}/tournaments/${activeTournament.value.id}/load-all-data?_t=${ts}`, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    })
    if (!res.ok) return
    const data = await res.json()
    const gp = data?.group_phase?.group_phase ?? data?.group_phase ?? {}
    liveGroupMatches.value = gp.matches || {}
    liveTeams.value = Array.isArray(data.teams) ? data.teams : []
    if (data.tournament?.tableCount) activeTournament.value.tableCount = data.tournament.tableCount
    else if (data.tournament?.table_count) activeTournament.value.tableCount = data.tournament.table_count
  } catch (e) { /* silent fail */ }
}

async function selectTournament(t) {
  activeTournament.value = t
  await store.load(t.id)
  activeTournament.value = store.tournament
  store.connect(t.id)
  carouselIndex.value = 0
  stopCarousel()
  startCarousel()
  // render QR
  await nextTick()
  if (qrCanvas.value && mobileUrl.value) {
    QRCode.toCanvas(qrCanvas.value, mobileUrl.value, { width: 200, color: { dark: '#ffffff', light: '#000000' } }).catch(() => {})
  }
  
  // Start Live-Polling für die 3D Tische
  fetchLiveTableData()
  if (pollingTimer) clearInterval(pollingTimer)
  pollingTimer = setInterval(fetchLiveTableData, 1000)
}

function deselectTournament() {
  activeTournament.value = null
  store.disconnect()
  stopCarousel()
  if (pollingTimer) clearInterval(pollingTimer)
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

/* Helfer für 3D Pyramiden & Spieler */
function buildPyramid(cupsArray, is10Cups) {
  const n = is10Cups ? 10 : 6
  const arr = (Array.isArray(cupsArray) && cupsArray.length > 0) ? cupsArray : Array(n).fill(true)
  if (is10Cups) {
    return [
      [ {idx:0, val:arr[0]}, {idx:1, val:arr[1]}, {idx:2, val:arr[2]}, {idx:3, val:arr[3]} ],
      [ {idx:4, val:arr[4]}, {idx:5, val:arr[5]}, {idx:6, val:arr[6]} ],
      [ {idx:7, val:arr[7]}, {idx:8, val:arr[8]} ],
      [ {idx:9, val:arr[9]} ]
    ]
  } else {
    return [
      [ {idx:0, val:arr[0]}, {idx:1, val:arr[1]}, {idx:2, val:arr[2]} ],
      [ {idx:3, val:arr[3]}, {idx:4, val:arr[4]} ],
      [ {idx:5, val:arr[5]} ]
    ]
  }
}

function formatPlayers(teamName) {
  const t = liveTeams.value.find(x => (x.name || x.teamName) === teamName)
  if (!t) return ''
  if (t.player1 && t.player2) return `${t.player1} & ${t.player2}`
  return t.player1 || t.player2 || ''
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
/* === 3D Isometrische Tisch Ansicht === */
.iso-table-container {
  perspective: 1200px;
  margin: 0 auto;
}
.iso-table {
  width: 220px;
  height: 380px;
  background: linear-gradient(to bottom, #11364d 0%, #1e6b52 100%);
  transform: rotateX(55deg);
  transform-style: preserve-3d;
  border: 6px solid #444;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 15px 0;
  box-shadow: 0 40px 30px rgba(0,0,0,0.6), inset 0 0 30px rgba(0,0,0,0.6);
  position: relative;
}
.iso-net {
  position: absolute;
  top: 50%;
  left: -5%;
  width: 110%;
  height: 4px;
  background: rgba(255,255,255,0.8);
  transform: translateY(-50%) translateZ(1px);
  box-shadow: 0 0 8px #fff;
}
.iso-cup-zone {
  height: 45%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  transform-style: preserve-3d;
}
.bottom-zone {
  flex-direction: column-reverse; /* Pyramide zeigt nach oben (zum Netz) */
}
.iso-cup-row {
  display: flex;
  gap: 12px;
  transform-style: preserve-3d;
}
.iso-cup {
  width: 26px;
  height: 26px;
  background: #e53935;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.9);
  transform: translateZ(10px) rotateX(-55deg); /* Kippt den Becher wieder hoch */
  box-shadow: 0 12px 10px rgba(0,0,0,0.5);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
}
.cup-inner {
  position: absolute;
  top: 15%; left: 15%;
  width: 70%; height: 70%;
  background: #8e0000;
  border-radius: 50%;
}
.iso-cup.is-hit {
  opacity: 0;
  transform: translateZ(-20px) rotateX(-55deg) scale(0.4);
}

.live-carousel-container {
  position: relative;
  width: 100%;
  overflow: hidden;
  padding: 10px 0;
}
.carousel-viewport {
  width: 100%;
  overflow: visible;
}
.carousel-track {
  display: flex;
  transition: transform 0.5s cubic-bezier(0.25, 1, 0.5, 1);
}
.carousel-slide {
  flex: 0 0 80%;
  padding: 0 10px;
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
  min-height: 320px;
  display: flex;
  flex-direction: column;
}
.dot-btn {
  width: 10px;
  height: 10px;
  padding: 0;
  border-radius: 50%;
}
</style>
