<template>
  <section class="ko-page mx-auto py-5 px-3">
    <!-- Header -->
    <div class="ko-header d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3 rounded-3 p-4 shadow-md border border-secondary border-opacity-50">
      <div class="d-flex flex-column flex-md-row align-items-md-center gap-4">
        <div>
          <h2 class="text-light mb-1 fs-4 fw-bold">KO-Phase</h2>
          <div class="text-secondary small opacity-75">
            Turnierbaum mit automatischer Fortschreibung der Sieger
          </div>
        </div>
        <div class="d-flex flex-wrap gap-2 text-light small">
          <span class="badge bg-secondary bg-opacity-75 rounded-pill px-3 py-2">
            <i class="bi bi-diagram-3 me-1"></i> {{ koSizeComputed }}er KO
          </span>
          <span class="badge bg-secondary bg-opacity-75 rounded-pill px-3 py-2">
            <i class="bi bi-cup-straw me-1"></i> {{ baseCupsPerGame }} Becher (Standard)
          </span>
          <span
            class="badge rounded-pill px-3 py-2"
            :class="finaleWith10Cups ? 'bg-warning text-dark' : 'bg-secondary bg-opacity-75 text-light'"
          >
            Finale & Platz 3: {{ finaleWith10Cups ? '10 Becher' : 'Standard' }}
          </span>
        </div>
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-sm btn-outline-light transition-all hover-scale" @click="$emit('back')">
          Zurück
        </button>
        <button
          class="btn btn-sm btn-outline-secondary transition-all hover-scale"
          @click="loadFromServer"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner-border spinner-border-sm" role="status"></span>
          <span v-else>Laden</span>
        </button>
        <button
          class="btn btn-sm btn-primary px-4 transition-all hover-scale"
          @click="saveToServer"
          :disabled="loading || roundsLocal.length === 0"
        >
          Speichern
        </button>
      </div>
    </div>

    <!-- Sieger Banner -->
    <div
      v-if="finalWinner"
      class="alert alert-success d-flex align-items-center justify-content-center py-3 mb-4 shadow-md rounded-pill ko-winner-banner"
    >
      <span class="fs-5 fw-bold">🏆 Turniersieger: {{ finalWinner }}</span>
    </div>

    <!-- Bracket -->
    <div class="ko-bracket-wrapper">
      <div class="card ko-bracket-card border-0 shadow-lg rounded-4 overflow-hidden">
        <div class="card-header d-flex justify-content-between align-items-center px-4 py-3 border-bottom border-secondary border-opacity-50 bg-dark bg-opacity-75">
          <span class="text-white-50 small fw-medium">
            Gesamtübersicht &amp; Eingabe der Ergebnisse
          </span>
          <span class="text-secondary small opacity-75">
            Horizontales Scrollen bei vielen Runden möglich
          </span>
        </div>
        <div class="card-body p-0 overflow-hidden position-relative bracket-container">
          <div class="bracket-gradient-overlay"></div>
          <div class="p-4 pt-3">
            <KnockoutBracket
              :rounds="roundsLocal"
              :readonly="false"
              :interactive="true"
              :cups-target-fn="cupsTargetForRound"
              @increment-cup="onBracketIncrementCup"
              @set-cups="onBracketSetCups"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Konfetti + Winner + Bracket -->
    <ConfettiOverlay
      :show="showConfetti"
      mode="burst"
      :durationMs="3500"
      :count="220"
      :colors="['#ff3366', '#33d1a0', '#ffd166', '#5ec8e2', '#ffffff']"
      :winnerName="finalWinner"          
      :rounds="roundsLocal"               
      :winnerDurationMs="10000"           
      @close="showConfetti = false"
    />
  </section>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue'
import KnockoutBracket from './KnockoutBracket.vue'
import ConfettiOverlay from './ConfettiOverlay.vue'

const API = import.meta.env.VITE_API_BASE || ''

const props = defineProps({
  tournamentId: { type: Number, required: true },
  teams: { type: Array, default: () => [] },
  koSize: { type: Number, default: null }
})

const emit = defineEmits(['back', 'saved'])

/* State */
const loading = ref(false)
const roundsLocal = reactive([])
const activeRoundIndex = ref(0)
const initialTeams = computed(() => (props.teams || []).filter(Boolean))

/* Settings */
const baseCupsPerGame = ref(6)
const finaleWith10Cups = ref(false)

/* Computed Helpers */
const currentRound = computed(() => roundsLocal[activeRoundIndex.value] || { matches: [] })
const POW2 = [4, 8, 16, 32, 64, 128]

const koSizeComputed = computed(() => {
  if (props.koSize) return props.koSize
  const n = initialTeams.value.length
  for (const k of POW2) if (k >= n) return k
  return n || 4
})

/**
 * Becher-Ziel:
 * - Normale Runden: baseCupsPerGame
 * - Finale UND Spiel um Platz 3: 10 Becher, wenn finaleWith10Cups = true
 */
function cupsTargetForRound(rIdx) {
  const round = roundsLocal[rIdx]
  if (!round) return baseCupsPerGame.value || 6

  const mainIndices = roundsLocal
    .map((r, idx) => ({ r, idx }))
    .filter(x => x.r.bracket_type !== 'placement')
    .map(x => x.idx)

  const finalIndex = mainIndices.length ? mainIndices[mainIndices.length - 1] : -1
  const isFinal = rIdx === finalIndex
  const isPlacement = round.bracket_type === 'placement'

  if ((isFinal || isPlacement) && finaleWith10Cups.value) {
    return 10
  }
  return baseCupsPerGame.value || 6
}

/* Winner Logic */
const showConfetti = ref(false)

const finalWinner = computed(() => {
  if (!roundsLocal.length) return null
  const mainRounds = roundsLocal.filter(r => r.bracket_type !== 'placement')
  if (!mainRounds.length) return null
  const last = mainRounds[mainRounds.length - 1]
  const fm = last?.matches?.[0]
  return (fm?.team1 && fm?.team2 && fm?.winner) ? fm.winner : null
})

watch(finalWinner, (v, oldV) => {
  if (v && v !== oldV) setTimeout(() => (showConfetti.value = true), 80)
})

function isRoundComplete(round) {
  if (!round || !round.matches.length) return false
  return round.matches.every(m => !m.team1 || !m.team2 || m.winner)
}

/* Helper Functions */
function roundNameFor(totalRounds, rIdx) {
  const labels = ['Runde der 128', 'Runde der 64', 'Runde der 32', 'Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale']
  const base = Math.max(0, labels.length - totalRounds)
  return labels[base + rIdx] || `Runde ${rIdx + 1}`
}

function seedPairs(teams, size) {
  const list = teams.slice(0, size)
  while (list.length < size) list.push(null)
  const pairs = []
  for (let i = 0; i < size / 2; i++) pairs.push([list[i], list[size - 1 - i]])
  return pairs
}

function buildEmptyRound(matchesCount) {
  return {
    bracket_type: 'main',
    round_name: '',
    matches: Array.from({ length: matchesCount }, () => ({
      team1: null,
      team2: null,
      winner: null,
      cups_team1: 0,
      cups_team2: 0
    }))
  }
}

function buildPlacementRound() {
  return {
    bracket_type: 'placement',
    round_name: 'Spiel um Platz 3',
    matches: [{
      team1: null,
      team2: null,
      winner: null,
      cups_team1: 0,
      cups_team2: 0
    }]
  }
}

function autoWinner(t1, t2) {
  if (t1 && !t2) return t1
  if (!t1 && t2) return t2
  return null
}
function safeNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function clampInt(v, min, max) {
  const n = parseInt(v, 10)
  const num = Number.isFinite(n) ? n : 0
  return Math.max(min, Math.min(max, num))
}

/* Logic: Cups & Propagation */
function applyWinnerRule(m, rIdx) {
  const a = safeNum(m.cups_team1)
  const b = safeNum(m.cups_team2)
  const target = cupsTargetForRound(rIdx)
  if (a >= target || b >= target) {
    if (a !== b) m.winner = a > b ? m.team1 : m.team2
  } else if (a === b) {
    m.winner = null
  }
}

/** Platz-3-Runde aus den Halbfinal-Verlierern befüllen */
function updatePlacementRound(roundsArr) {
  const placementIdx = roundsArr.findIndex(r => r.bracket_type === 'placement')
  if (placementIdx === -1) return

  const placement = roundsArr[placementIdx]
  if (!placement?.matches?.length) return

  const match = placement.matches[0]

  const mainInfos = roundsArr
    .map((r, idx) => ({ r, idx }))
    .filter(x => x.r.bracket_type !== 'placement')

  if (mainInfos.length < 2) return

  const semiIdx = mainInfos[mainInfos.length - 2].idx
  const semiRound = roundsArr[semiIdx]
  if (!semiRound) return

  const losers = []
  semiRound.matches.forEach(m => {
    if (!m.team1 || !m.team2) return
    const w = m.winner || autoWinner(m.team1, m.team2)
    if (!w) return
    const loser = w === m.team1 ? m.team2 : m.team1
    if (loser) losers.push(loser)
  })

  const newTeam1 = losers[0] || null
  const newTeam2 = losers[1] || null

  const sameTeams = (match.team1 === newTeam1 && match.team2 === newTeam2)
  if (!sameTeams) {
    match.cups_team1 = 0
    match.cups_team2 = 0
    match.winner = null
  }

  match.team1 = newTeam1
  match.team2 = newTeam2
}

function propagateAll(rounds) {
  for (let r = 0; r < rounds.length - 1; r++) {
    const cur = rounds[r]
    const nxt = rounds[r + 1]
    if (!cur || !nxt) continue
    if (cur.bracket_type !== 'main' || nxt.bracket_type !== 'main') continue

    nxt.matches.forEach(mm => {
      mm.team1 = null
      mm.team2 = null
      mm.winner = null
    })

    cur.matches.forEach((m, idx) => {
      const w = m.winner || autoWinner(m.team1, m.team2)
      if (!w) return
      const tIdx = Math.floor(idx / 2)
      const pos = (idx % 2 === 0) ? 'team1' : 'team2'
      nxt.matches[tIdx][pos] = w
    })
  }
  updatePlacementRound(rounds)
}

/* Seeding inkl. Platz 3 */
function seedBracket() {
  const size = koSizeComputed.value
  if (!size || size < 2) return

  const totalRounds = Math.max(1, Math.log2(size) | 0)
  const pairs = seedPairs(initialTeams.value, size)

  const rounds = []

  // Runde 1
  rounds.push({
    bracket_type: 'main',
    round_name: roundNameFor(totalRounds, 0),
    matches: pairs.map(p => ({
      team1: p[0],
      team2: p[1],
      winner: autoWinner(p[0], p[1]),
      cups_team1: 0,
      cups_team2: 0
    }))
  })

  // weitere Haupt-Runden
  for (let r = 1, m = pairs.length >> 1; r < totalRounds; r++, m >>= 1) {
    const empty = buildEmptyRound(Math.max(1, m))
    empty.round_name = roundNameFor(totalRounds, r)
    rounds.push(empty)
  }

  // Spiel um Platz 3 (ab 4er KO)
  if (size >= 4) {
    rounds.push(buildPlacementRound())
  }

  propagateAll(rounds)
  roundsLocal.splice(0, roundsLocal.length, ...rounds)
  activeRoundIndex.value = 0
}

/* Actions für Cups */
function setCups(rIdx, mIdx, teamField, raw) {
  const m = roundsLocal[rIdx]?.matches?.[mIdx]
  if (!m) return
  const key = (teamField === 'team1') ? 'cups_team1' : 'cups_team2'
  m[key] = clampInt(raw, 0, cupsTargetForRound(rIdx))
  applyWinnerRule(m, rIdx)
  recalcPropagation(rIdx)
  saveSingleKoMatch(rIdx, mIdx, m)
}

function incrementCup(rIdx, mIdx, teamKey) {
  const m = roundsLocal[rIdx]?.matches?.[mIdx]
  if (!m) return
  const key = (teamKey === 'team1') ? 'cups_team1' : 'cups_team2'
  m[key] = clampInt(safeNum(m[key]) + 1, 0, cupsTargetForRound(rIdx))
  applyWinnerRule(m, rIdx)
  recalcPropagation(rIdx)
  saveSingleKoMatch(rIdx, mIdx, m)
}

function recalcPropagation(startRIdx) {
  for (let rr = startRIdx; rr < roundsLocal.length - 1; rr++) {
    const cur = roundsLocal[rr]
    const nxt = roundsLocal[rr + 1]
    if (!cur || !nxt) continue
    if (cur.bracket_type !== 'main' || nxt.bracket_type !== 'main') continue

    nxt.matches.forEach(mm => {
      mm.team1 = null
      mm.team2 = null
      mm.winner = null
    })

    cur.matches.forEach((mm, idx) => {
      const w = mm.winner || autoWinner(mm.team1, mm.team2)
      if (!w) return
      const tIdx = Math.floor(idx / 2)
      const pos = (idx % 2 === 0) ? 'team1' : 'team2'
      nxt.matches[tIdx][pos] = w
    })
  }
  updatePlacementRound(roundsLocal)
}

/* Events vom Bracket */
function onBracketSetCups({ roundIndex, matchIndex, team, value }) {
  setCups(roundIndex, matchIndex, team, value)
}
function onBracketIncrementCup({ roundIndex, matchIndex, team }) {
  incrementCup(roundIndex, matchIndex, team)
}

/* Server I/O */
async function loadFromServer() {
  loading.value = true
  try {
    const [resBracket, resData] = await Promise.all([
      fetch(`${API}/tournaments/${props.tournamentId}/load-ko-bracket`).catch(() => null),
      fetch(`${API}/tournaments/${props.tournamentId}/load-all-data`).catch(() => null)
    ])

    if (resData && resData.ok) {
      const tData = await resData.json()
      const t = tData?.tournament ?? {}
      baseCupsPerGame.value = Number.isFinite(+t.cupsPerGame) ? +t.cupsPerGame : 6
      finaleWith10Cups.value = !!t.finaleWith10Cups
    }

    let serverRounds = []
    if (resBracket && resBracket.ok) {
      serverRounds = (await resBracket.json())?.rounds || []
    }

    if (serverRounds.length > 0) {
      let all = serverRounds.map(r => ({
        bracket_type: r.bracket_type || 'main',
        round_name: r.round_name || '',
        matches: (r.matches || []).map(m => ({
          team1: m.team1 ?? null,
          team2: m.team2 ?? null,
          winner: m.winner ?? null,
          cups_team1: +m.cups_team1 || 0,
          cups_team2: +m.cups_team2 || 0
        }))
      }))

      let mainRounds = all.filter(r => r.bracket_type !== 'placement')
      let placementRounds = all.filter(r => r.bracket_type === 'placement')

      const derivedSize = Math.max(2, (mainRounds[0]?.matches?.length || 1) * 2)
      const size = props.koSize || derivedSize
      const totalRounds = Math.max(1, Math.log2(size) | 0)

      if (mainRounds.length < totalRounds) {
        for (let i = mainRounds.length; i < totalRounds; i++) {
          const prevLen = mainRounds[mainRounds.length - 1]?.matches?.length || 2
          mainRounds.push(buildEmptyRound(Math.max(1, prevLen >> 1)))
        }
      }

      let mainIdx = 0
      mainRounds = mainRounds.map(r => ({
        ...r,
        round_name: roundNameFor(totalRounds, mainIdx++)
      }))

      if (!placementRounds.length && size >= 4) {
        placementRounds.push(buildPlacementRound())
      }

      const rounds = [...mainRounds, ...placementRounds]
      propagateAll(rounds)
      roundsLocal.splice(0, roundsLocal.length, ...rounds)

      const firstIncomplete = roundsLocal.findIndex(r => !isRoundComplete(r))
      activeRoundIndex.value = firstIncomplete >= 0 ? firstIncomplete : (roundsLocal.length - 1)
    } else if (initialTeams.value.length > 0) {
      seedBracket()
    }
  } catch (e) {
    console.error(e)
    if (roundsLocal.length === 0 && initialTeams.value.length > 0) seedBracket()
  } finally {
    loading.value = false
  }
}

async function saveToServer() {
  loading.value = true
  try {
    const payload = { rounds: roundsLocal }
    await fetch(`${API}/tournaments/${props.tournamentId}/save-ko-bracket`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    emit('saved')
    if (finalWinner.value) showConfetti.value = true
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function saveSingleKoMatch(rIdx, mIdx, m) {
  try {
    const body = {
      round_index: rIdx,
      match_index: mIdx,
      round_name: roundsLocal[rIdx]?.round_name || '',
      ...m
    }
    const res = await fetch(`${API}/tournaments/${props.tournamentId}/ko-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!res.ok && res.status !== 404) throw new Error('Failed single save')
    if (res.status === 404) await saveToServer()
  } catch (e) {
    console.error(e)
  }
}

function applyRounds(newRounds) {
  roundsLocal.splice(0, roundsLocal.length, ...(newRounds ?? []))
}

onMounted(async () => {
  await loadFromServer()
})
</script>

<style scoped>
.ko-page {
  max-width: 1300px;
  background: radial-gradient(circle at top left, #343a40 0, #121212 45%, #000 100%);
}

/* Header */
.ko-header {
  background: rgba(18, 18, 18, 0.95);
  border: 1px solid rgba(108, 117, 125, 0.6);
  transition: box-shadow 0.3s ease;
}
.ko-header:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Siegerbanner */
.ko-winner-banner {
  border: 1px solid rgba(25, 135, 84, 0.7);
  background: linear-gradient(to right, #198754, #146c43);
  color: #fff;
}

/* Bracket Card */
.ko-bracket-wrapper {
  display: flex;
  justify-content: center;
}
.ko-bracket-card {
  width: 100%;
  max-width: 1250px;
  background: #141414;
  border: 1px solid rgba(108, 117, 125, 0.5);
  transition: box-shadow 0.3s ease;
}
.ko-bracket-card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

/* Container – keine künstliche Höhe, der Inhalt darf nach unten wachsen */
.bracket-container {
  overflow-y: visible;
  overflow-x: hidden;
}

/* dezenter Overlay-Verlauf oben */
.bracket-gradient-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at top left, rgba(255, 255, 255, 0.05), transparent 60%);
}

/* Utilities */
.transition-all {
  transition: all 0.2s ease;
}
.hover-scale:hover {
  transform: scale(1.05);
}
.shadow-md {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
</style>
