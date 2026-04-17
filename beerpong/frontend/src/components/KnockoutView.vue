<template>
  <section class="ko-page mx-auto py-5 px-3">
    <!-- Header -->
    <div class="ko-header d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3 rounded-3 p-4 shadow-md border border-secondary border-opacity-50">
      <div class="d-flex flex-column flex-md-row align-items-md-center gap-4">
        <div>
          <h2 class="text-light mb-1 fs-4 fw-bold">KO-Phase</h2>
          <div class="text-secondary small opacity-75">
            Turnierbaum nach Preview-Plan mit manueller Rundenfreigabe
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
            Finale: {{ finaleWith10Cups ? '10 Becher' : 'Standard' }}
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

    <!-- Ansichts-Umschalter -->
    <div class="btn-group mb-4 w-100 shadow-sm">
      <input type="radio" class="btn-check" id="ko-tab-tables" value="tables" v-model="viewMode">
      <label class="btn btn-outline-info" for="ko-tab-tables">🏓 Live-Spiele</label>

      <input type="radio" class="btn-check" id="ko-tab-bracket" value="bracket" v-model="viewMode">
      <label class="btn btn-outline-info" for="ko-tab-bracket">🏆 Turnierbaum</label>
    </div>

    <!-- ======= LIVE-SPIELE TAB ======= -->
    <div v-show="viewMode === 'tables'">
      <!-- Tisch-Verwaltung -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0 text-light">Aktive Tische ({{ tableCount }})</h5>
        <div class="btn-group">
          <button class="btn btn-sm btn-outline-secondary" @click="removeTable" :disabled="tableCount <= 1">− Tisch entfernen</button>
          <button class="btn btn-sm btn-outline-secondary" @click="addTable" :disabled="tableCount >= 8">+ Tisch hinzufügen</button>
        </div>
      </div>

      <div class="card bg-dark border-secondary text-light mb-4">
        <div class="card-body d-flex flex-column flex-lg-row justify-content-between align-items-lg-center gap-3">
          <div>
            <div class="text-secondary small text-uppercase" style="letter-spacing:.08em">Aktive KO-Stufe</div>
            <div class="fw-bold fs-5">{{ activeStageLabel }}</div>
            <div class="text-secondary small">
              {{ currentRoundProgressText }}
            </div>
          </div>
          <div class="d-flex flex-wrap gap-2 align-items-center">
            <span
              v-if="activeStageMeta.currentRoundComplete"
              class="badge bg-success-subtle text-success border border-success-subtle px-3 py-2"
            >
              Runde abgeschlossen
            </span>
            <span
              v-else
              class="badge bg-secondary bg-opacity-75 text-light px-3 py-2"
            >
              Runde läuft
            </span>
            <button
              v-if="activeStageMeta.hasNextStage"
              class="btn btn-sm btn-success"
              @click="startNextKoRound"
              :disabled="loading || !canStartNextKoRound"
            >
              {{ nextStageButtonLabel }}
            </button>
          </div>
        </div>
      </div>

      <!-- Aktive Tische mit klickbaren Bechern -->
      <div v-if="liveMatchControls.length" class="ko-live-tables">
        <div v-for="ctrl in liveMatchControls" :key="ctrl.matchId" class="ko-live-table-wrap">
          <div class="d-flex justify-content-between align-items-center mb-2 px-1">
            <h4 class="text-warning mb-0 fw-bold">Tisch {{ ctrl.tableNo }}</h4>
            <span class="badge bg-secondary">{{ ctrl.roundName }}</span>
          </div>

          <!-- Schützenauswahl Overlay -->
          <div v-if="pendingKoShooter && pendingKoShooter.matchId === ctrl.matchId"
               class="p-4 border border-warning rounded bg-dark text-center shadow-lg ko-shooter-overlay">
            <h5 class="text-warning mb-3">
              {{ pendingKoShooter.mode === 'overtime_credit' ? `Nachwurf für ${pendingKoShooter.shooterTeamName}!` : `Treffer für ${pendingKoShooter.shooterTeamName}!` }}
            </h5>
            <template v-if="pendingKoShooter.mode === 'overtime_credit'">
              <p class="text-light mb-2">
                Verteile die {{ pendingKoShooter.bonusCupCount }} Nachwurf-Becher auf die Spieler.
              </p>
              <div class="text-secondary small mb-4">
                Noch zu verteilen: {{ getKoOvertimeRemainingCups() }}
              </div>
              <div class="d-flex justify-content-center gap-3 flex-wrap mb-4">
                <div v-if="pendingKoShooter.p1" class="ko-credit-card">
                  <div class="text-light fw-semibold mb-2">{{ pendingKoShooter.p1 }}</div>
                  <div class="btn-group" role="group" aria-label="Nachwurf Spieler 1">
                    <button class="btn btn-outline-secondary" @click="adjustKoOvertimeAllocation('p1', -1)" :disabled="(pendingKoShooter.bonusP1 || 0) <= 0">−</button>
                    <span class="btn btn-outline-light disabled ko-credit-count">{{ pendingKoShooter.bonusP1 || 0 }}</span>
                    <button class="btn btn-outline-warning" @click="adjustKoOvertimeAllocation('p1', 1)" :disabled="getKoOvertimeRemainingCups() <= 0">+</button>
                  </div>
                </div>
                <div v-if="pendingKoShooter.p2" class="ko-credit-card">
                  <div class="text-light fw-semibold mb-2">{{ pendingKoShooter.p2 }}</div>
                  <div class="btn-group" role="group" aria-label="Nachwurf Spieler 2">
                    <button class="btn btn-outline-secondary" @click="adjustKoOvertimeAllocation('p2', -1)" :disabled="(pendingKoShooter.bonusP2 || 0) <= 0">−</button>
                    <span class="btn btn-outline-light disabled ko-credit-count">{{ pendingKoShooter.bonusP2 || 0 }}</span>
                    <button class="btn btn-outline-warning" @click="adjustKoOvertimeAllocation('p2', 1)" :disabled="getKoOvertimeRemainingCups() <= 0">+</button>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <p class="text-light mb-4">Wer hat den Becher getroffen?</p>
              <div class="d-flex justify-content-center gap-3 mb-4">
                <button v-if="pendingKoShooter.p1" class="btn btn-lg px-4 py-3 fw-bold"
                        :class="selectedKoPlayer === pendingKoShooter.p1 ? 'btn-success' : 'btn-outline-success'"
                        @click="selectKoShooter(pendingKoShooter.p1)">{{ pendingKoShooter.p1 }}</button>
                <button v-if="pendingKoShooter.p2" class="btn btn-lg px-4 py-3 fw-bold"
                        :class="selectedKoPlayer === pendingKoShooter.p2 ? 'btn-success' : 'btn-outline-success'"
                        @click="selectKoShooter(pendingKoShooter.p2)">{{ pendingKoShooter.p2 }}</button>
              </div>
            </template>
            <div class="d-flex justify-content-center gap-2">
              <button class="btn btn-outline-secondary" @click="cancelKoShooter">
                {{ pendingKoShooter.mode === 'overtime_credit' ? 'Zurück' : 'Abbruch (Undo)' }}
              </button>
              <button class="btn btn-primary btn-lg px-5 fw-bold" :disabled="pendingKoShooter.mode === 'overtime_credit' ? !isKoOvertimeAllocationComplete() : !selectedKoPlayer" @click="confirmKoShooter">
                {{ pendingKoShooter.mode === 'overtime_credit' ? 'Nachwurf Bestätigen' : 'Treffer Bestätigen' }}
              </button>
            </div>
          </div>

          <!-- Spielabschluss-Dialog -->
          <div v-else-if="pendingKoConclusion && pendingKoConclusion.matchId === ctrl.matchId"
               class="p-5 border border-primary rounded bg-dark text-center shadow-lg ko-shooter-overlay">
            <h4 class="text-primary mb-4">Spielabschluss</h4>

            <template v-if="pendingKoConclusion.step === 'NACHWURF'">
              <p class="text-light mb-4 fs-5">Alle Becher getroffen! Gibt es einen <strong>Nachwurf</strong>?</p>
              <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-lg btn-primary px-4 fw-bold" @click="conclusionKoStep('ALL_HIT')">Ja (Nachwurf)</button>
                <button class="btn btn-lg btn-outline-primary px-4 fw-bold" @click="conclusionKoStep('END_QUERY')">Nein (Direkter Sieg)</button>
              </div>
            </template>

            <template v-else-if="pendingKoConclusion.step === 'ALL_HIT'">
              <p class="text-light mb-4 fs-5">Wurden beim Nachwurf <strong>alle verbleibenden Becher</strong> getroffen?</p>
              <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-lg btn-warning px-4 fw-bold" @click="conclusionKoOvertime">Ja (Verlängerung 3 Becher)</button>
                <button class="btn btn-lg btn-outline-primary px-4 fw-bold" @click="conclusionKoStep('END_QUERY')">Nein (Sieg nach Nachwurf)</button>
              </div>
            </template>

            <template v-else-if="pendingKoConclusion.step === 'END_QUERY'">
              <p class="text-light mb-4 fs-5">Soll das Spiel jetzt <strong>final beendet</strong> werden?</p>
              <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-lg btn-success px-4 fw-bold" @click="finishKoConclusion(true)">Ja (Spiel abschließen)</button>
                <button class="btn btn-lg btn-outline-danger px-4 fw-bold" @click="finishKoConclusion(false)">Nein (Zurück zum Spielstand)</button>
              </div>
            </template>

            <button v-if="pendingKoConclusion.step !== 'NACHWURF'" class="btn btn-sm btn-outline-secondary mt-4" @click="conclusionKoBack">← Zurück</button>
            <button v-else class="btn btn-sm btn-outline-secondary mt-4" @click="pendingKoConclusion = null">Abbrechen</button>
          </div>

          <!-- Normale Becheransicht -->
          <MatchTableControls
            v-else
            :tournament-id="tournamentId"
            :match-id="ctrl.matchId"
            :team1-name="ctrl.team1Name"
            :team2-name="ctrl.team2Name"
            :is10-cups="ctrl.is10Cups"
            :cups-state-team1="ctrl.cupsStateTeam1"
            :cups-state-team2="ctrl.cupsStateTeam2"
            :team1-rerack-used="ctrl.rerackUsedTeam1"
            :team2-rerack-used="ctrl.rerackUsedTeam2"
            @cup-hit="onKoCupHit"
            @undo="onKoUndo"
            @rerack="onKoRerack"
          />
        </div>
      </div>
      <div v-else class="alert alert-dark border-secondary text-secondary">
        Keine aktiven Spiele – warte auf Teams oder Ergebnisse der vorherigen Runde.
      </div>

      <!-- Upcoming matches -->
      <div v-if="upcomingControls.length" class="mt-4">
        <h6 class="text-secondary mb-2">Nächste Spiele</h6>
        <div class="list-group list-group-flush">
          <div v-for="ctrl in upcomingControls" :key="ctrl.matchId"
               class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
            <span>{{ ctrl.team1Name }} vs. {{ ctrl.team2Name }}</span>
            <span class="badge bg-secondary">{{ ctrl.roundName }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ======= TURNIERBAUM TAB ======= -->
    <div v-show="viewMode === 'bracket'" class="ko-tab-root pt-2 pb-3 px-2">
      <div class="ko-section-head mb-2 px-1 border-bottom border-secondary pb-1">
        🏆 K.O.-Phase
      </div>

      <div v-if="roundsLocal.length" class="ko-bracket-wrap">
        <KnockoutResultsTree
          :rounds="roundsLocal"
          :active-match-ids="activeMatchIds"
        />
      </div>
      <div v-else class="px-2 text-secondary">
        K.O.-Phase noch nicht verfügbar.
      </div>

      <!-- Manuelle Ergebnis-Eingabe (ausklappbar) -->
      <details class="ko-manual-panel mt-4">
        <summary class="ko-manual-panel__summary text-secondary small">
          ▸ Manuelle Ergebnis-Eingabe (Becher-Zahlen direkt setzen)
        </summary>
        <div class="ko-manual-panel__body mt-2 p-3 bg-dark rounded border border-secondary overflow-auto">
          <KnockoutBracket
            :rounds="roundsLocal"
            :readonly="false"
            :interactive="true"
            :cups-target-fn="cupsTargetForRound"
            :active-match-ids="activeMatchIds"
            @increment-cup="onBracketIncrementCup"
            @set-cups="onBracketSetCups"
          />
        </div>
      </details>
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
import KnockoutResultsTree from './KnockoutResultsTree.vue'
import ConfettiOverlay from './ConfettiOverlay.vue'
import MatchTableControls from './MatchTableControls.vue'
import { useTournamentStore } from '../stores/tournament.js'
import { makeCupsStateFromCount } from '../utils/tableAssignments.js'
import { filterKoRoundsForActiveStage, getKoMainRoundInfos, getKoStageMeta } from '../utils/koDisplay.js'

const API = import.meta.env.VITE_API_BASE || ''
const store = useTournamentStore()

const props = defineProps({
  tournamentId: { type: Number, required: true },
  teams: { type: Array, default: () => [] },
  koSize: { type: Number, default: null },
  teamPlayers: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['back', 'saved'])

/* State */
const loading = ref(false)
const roundsLocal = reactive([])
const activeMainRoundIndex = ref(0)
const activeStageKind = ref('main')
const initialTeams = computed(() => (props.teams || []).filter(Boolean))
const tableCount = ref(2)
const viewMode = ref('tables')

/** Schützenauswahl: { mode, matchId, rIdx, mIdx, teamKey, cupIndex, shooterTeamName, p1, p2, bonusCupCount } | null */
const pendingKoShooter = ref(null)
const selectedKoPlayer = ref(null)

/** Spielabschluss-Dialog: { matchId, rIdx, mIdx, teamKey, step, history } | null */
const pendingKoConclusion = ref(null)

/* Settings */
const baseCupsPerGame = ref(6)
const finaleWith10Cups = ref(false)

/* Table management */
const _tableCountLoading = ref(true)  // suppress watch during initial load
function addTable() { tableCount.value = Math.min(8, tableCount.value + 1) }
function removeTable() { tableCount.value = Math.max(1, tableCount.value - 1) }

watch(tableCount, async (newCount) => {
  if (_tableCountLoading.value || !props.tournamentId) return
  try {
    await fetch(`${API}/tournaments/${props.tournamentId}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tableCount: newCount }),
    })
  } catch { /* silent */ }
})

const activeStageMeta = computed(() => getKoStageMeta(roundsLocal, activeMainRoundIndex.value, activeStageKind.value))
const activeStageLabel = computed(() => activeStageMeta.value.currentRoundLabel || 'KO-Phase')
const currentRoundProgressText = computed(() => {
  const stageRounds = filterKoRoundsForActiveStage(roundsLocal, activeMainRoundIndex.value, activeStageKind.value)
  const matches = stageRounds[0]?.matches || []
  const playableMatches = matches.filter(match => match?.team1 && match?.team2)
  const finishedMatches = playableMatches.filter(match => !!match?.winner)
  if (!playableMatches.length) return 'Warte auf Teams'
  return `${finishedMatches.length}/${playableMatches.length} Spiele beendet`
})
const canStartNextKoRound = computed(() => activeStageMeta.value.hasNextStage && activeStageMeta.value.currentRoundComplete)
const nextStageButtonLabel = computed(() =>
  activeStageMeta.value.nextRoundLabel ? `${activeStageMeta.value.nextRoundLabel} starten` : 'Nächste Runde starten'
)
const playableRoundIndices = computed(() => {
  const rounds = filterKoRoundsForActiveStage(roundsLocal, activeMainRoundIndex.value, activeStageKind.value)
  return new Set(
    rounds
      .map(round => roundsLocal.indexOf(round))
      .filter(idx => idx >= 0)
  )
})

function serializeKoRoundForRelease(round) {
  if (!round) return null
  return {
    bracket_type: round.bracket_type || 'main',
    round_name: round.round_name || '',
    matches: (round.matches || [])
      .map((match, idx) => ({
        ko_match_index: Number.isInteger(Number(match?.ko_match_index))
          ? Number(match.ko_match_index)
          : idx,
        team1: match?.team1 || null,
        team2: match?.team2 || null,
      }))
      .filter(match => match.team1 && match.team2),
  }
}

function koWinnerFor(match) {
  return match?.winner || autoWinner(match?.team1, match?.team2)
}

function isKoMatchStartedLocal(match) {
  if (!match) return false
  if (match.winner) return true
  if (safeNum(match.cups_team1) > 0 || safeNum(match.cups_team2) > 0) return true
  if (match.is_overtime) return true
  return Number.isFinite(Number(match.table_no)) && Number(match.table_no) > 0
}

function resetKoMatchProgress(match) {
  if (!match) return
  match.winner = null
  match.cups_team1 = 0
  match.cups_team2 = 0
  match.cups_state_team1 = null
  match.cups_state_team2 = null
  match.is_overtime = false
  match.table_no = null
  match.rerack_used_team1 = false
  match.rerack_used_team2 = false
}

function syncNextRoundFromCurrent(curRound, nextRound) {
  const currentMatches = curRound?.matches || []
  const nextMatches = nextRound?.matches || []
  nextMatches.forEach((nextMatch, idx) => {
    if (!nextMatch || isKoMatchStartedLocal(nextMatch)) return
    const sourceA = currentMatches[idx * 2] || null
    const sourceB = currentMatches[idx * 2 + 1] || null
    const desiredTeam1 = koWinnerFor(sourceA) || null
    const desiredTeam2 = koWinnerFor(sourceB) || null
    const teamsChanged = nextMatch.team1 !== desiredTeam1 || nextMatch.team2 !== desiredTeam2
    if (!teamsChanged) return
    nextMatch.team1 = desiredTeam1
    nextMatch.team2 = desiredTeam2
    resetKoMatchProgress(nextMatch)
  })
}

function buildNextMainRoundForRelease(mainInfoIndex) {
  const mainInfos = getKoMainRoundInfos(roundsLocal)
  const targetInfo = mainInfos[mainInfoIndex]
  if (!targetInfo) return null
  if (mainInfoIndex === 0) return serializeKoRoundForRelease(targetInfo.round)
  const previousRound = mainInfos[mainInfoIndex - 1]?.round
  const matches = (targetInfo.round?.matches || [])
    .map((match, idx) => {
      const sourceA = previousRound?.matches?.[idx * 2]
      const sourceB = previousRound?.matches?.[idx * 2 + 1]
      const team1 = koWinnerFor(sourceA)
      const team2 = koWinnerFor(sourceB)
      if (!team1 || !team2 || team1 === team2) return null
      return {
        ko_match_index: Number.isInteger(Number(match?.ko_match_index))
          ? Number(match.ko_match_index)
          : idx,
        team1,
        team2,
      }
    })
    .filter(Boolean)

  return {
    bracket_type: targetInfo.round?.bracket_type || 'main',
    round_name: targetInfo.round?.round_name || '',
    matches,
  }
}

function buildPlacementRoundForRelease() {
  const placementRound = roundsLocal.find(round => round?.bracket_type === 'placement')
  if (!placementRound) return null
  const mainInfos = getKoMainRoundInfos(roundsLocal)
  if (mainInfos.length < 2) return null
  const semifinalRound = mainInfos[mainInfos.length - 2]?.round
  const losers = (semifinalRound?.matches || [])
    .map(match => {
      const winner = koWinnerFor(match)
      if (!winner || !match?.team1 || !match?.team2) return null
      return winner === match.team1 ? match.team2 : match.team1
    })
    .filter(Boolean)

  if (losers.length < 2 || losers[0] === losers[1]) return null
  const placementMatch = placementRound.matches?.[0] || {}

  return {
    bracket_type: placementRound.bracket_type || 'placement',
    round_name: placementRound.round_name || 'Spiel um Platz 3',
    matches: [{
      ko_match_index: Number.isInteger(Number(placementMatch?.ko_match_index))
        ? Number(placementMatch.ko_match_index)
        : 0,
      team1: losers[0],
      team2: losers[1],
    }],
  }
}

/* Undo history per match+team: Map<"rIdx:mIdx:teamKey", number[]> */
const koUndoHistory = ref(new Map())

/* All pending matches (both teams, no winner), in bracket order */
const allPendingControls = computed(() => {
  const result = []
  roundsLocal.forEach((round, rIdx) => {
    if (!playableRoundIndices.value.has(rIdx)) return
    round.matches?.forEach((m, mIdx) => {
      if (!m.team1 || !m.team2 || m.winner) return
      const cupsTarget = cupsTargetForRound(rIdx)
      const state1 = normalizeKoStateArray(m.cups_state_team1, cupsTarget, m.cups_team2, !!m.is_overtime)
      const state2 = normalizeKoStateArray(m.cups_state_team2, cupsTarget, m.cups_team1, !!m.is_overtime)
      result.push({
        matchId: `${rIdx}:${mIdx}`,
        rIdx, mIdx,
        team1Name: m.team1,
        team2Name: m.team2,
        persistedTableNo: Number.isFinite(Number(m.table_no)) && Number(m.table_no) > 0 ? Number(m.table_no) : null,
        cupsStateTeam1: state1,
        cupsStateTeam2: state2,
        is10Cups: cupsTarget === 10,
        roundName: round.round_name || 'KO-Phase',
        rerackUsedTeam1: !!m.rerack_used_team1,
        rerackUsedTeam2: !!m.rerack_used_team2,
      })
    })
  })
  return result
})

/* Stable table assignments — once a match is at table N, it stays until finished */
const koTableMap = ref(new Map())  // matchId -> tableNo (reactive, for template)
let _prevKoTableMap = new Map()    // non-reactive mirror to avoid circular deps

watch(
  [allPendingControls, tableCount],
  ([pending, maxTables]) => {
    const newMap = new Map()
    const usedTables = new Set()

    // Pass 0: honor persisted assignments from backend or previous sync
    for (const ctrl of pending) {
      const tableNo = ctrl.persistedTableNo
      if (!tableNo || tableNo < 1 || tableNo > maxTables) continue
      if (newMap.has(ctrl.matchId) || usedTables.has(tableNo)) continue
      newMap.set(ctrl.matchId, tableNo)
      usedTables.add(tableNo)
    }

    // Pass 1: keep existing assignments for still-pending matches
    for (const [key, tableNo] of _prevKoTableMap.entries()) {
      if (tableNo < 1 || tableNo > maxTables) continue
      if (newMap.has(key) || usedTables.has(tableNo)) continue
      if (pending.find(c => c.matchId === key)) {
        newMap.set(key, tableNo)
        usedTables.add(tableNo)
      }
    }

    // Pass 2: assign new pending matches to free tables in order
    const unassigned = pending.filter(c => !newMap.has(c.matchId))
    let uIdx = 0
    for (let t = 1; t <= maxTables && uIdx < unassigned.length; t++) {
      if (!usedTables.has(t)) {
        newMap.set(unassigned[uIdx].matchId, t)
        usedTables.add(t)
        uIdx++
      }
    }

    _prevKoTableMap = newMap
    koTableMap.value = newMap
  },
  { deep: true, immediate: true }
)

/* Live match controls — only assigned tables, sorted by table number */
const liveMatchControls = computed(() => {
  const byTable = new Map()
  for (const ctrl of allPendingControls.value) {
    const t = koTableMap.value.get(ctrl.matchId)
    if (t !== undefined) byTable.set(t, ctrl)
  }
  const result = []
  for (let t = 1; t <= tableCount.value; t++) {
    const ctrl = byTable.get(t)
    if (ctrl) result.push({ ...ctrl, tableNo: t })
  }
  return result
})

const activeMatchIds = computed(() => new Set(
  liveMatchControls.value
    .map(ctrl => roundsLocal[ctrl.rIdx]?.matches?.[ctrl.mIdx]?.id)
    .filter(id => id != null)
))

/* Remaining matches not yet at a table */
const assignedIds = computed(() => new Set(liveMatchControls.value.map(c => c.matchId)))
const upcomingControls = computed(() =>
  allPendingControls.value.filter(c => !assignedIds.value.has(c.matchId))
)

watch(
  liveMatchControls,
  controls => {
    controls.forEach(ctrl => {
      const match = roundsLocal[ctrl.rIdx]?.matches?.[ctrl.mIdx]
      if (!match) return
      const currentTableNo = Number.isFinite(Number(match.table_no)) && Number(match.table_no) > 0
        ? Number(match.table_no)
        : null
      if (currentTableNo === ctrl.tableNo) return
      match.table_no = ctrl.tableNo
      saveSingleKoMatch(ctrl.rIdx, ctrl.mIdx, match)
    })
  },
  { deep: true, immediate: true }
)

function _findKoMatch(matchId) {
  const [rStr, mStr] = String(matchId).split(':')
  const rIdx = Number(rStr)
  const mIdx = Number(mStr)
  return { rIdx, mIdx, m: roundsLocal[rIdx]?.matches?.[mIdx] ?? null }
}

function resolveKoTeamPlayers(teamName) {
  if (!teamName) return { p1: null, p2: null }
  const normalized = teamName.trim().toLowerCase()
  const mergedTeamPlayers = {
    ...(store.teamPlayers || {}),
    ...(props.teamPlayers || {}),
  }
  const allPlayerKeys = Object.keys(mergedTeamPlayers)
  const exactKey = allPlayerKeys.find(k => k.trim().toLowerCase() === normalized)
  const players = mergedTeamPlayers[exactKey || teamName] || {}
  return {
    p1: players.player1 || null,
    p2: players.player2 || null,
  }
}

function buildFrontOvertimeState(size, rawState = null) {
  const state = Array(size).fill(false)
  const source = Array.isArray(rawState) ? rawState : [true, true, true]
  const indices = size >= 10 ? [9, 7, 8] : size >= 6 ? [5, 3, 4] : Array.from({ length: Math.min(3, size) }, (_, idx) => Math.max(0, size - Math.min(3, size) + idx))
  indices.forEach((targetIdx, idx) => {
    if (targetIdx < size) state[targetIdx] = !!source[idx]
  })
  return state
}

function normalizeKoStateArray(rawState, cupsTarget, hitsTaken = 0, isOvertime = false) {
  if (Array.isArray(rawState) && rawState.length === cupsTarget) {
    return [...rawState]
  }
  if (isOvertime && Array.isArray(rawState) && rawState.length === 3 && cupsTarget > 3) {
    return buildFrontOvertimeState(cupsTarget, rawState)
  }
  return makeCupsStateFromCount(hitsTaken, cupsTarget)
}

function getKoStandingCups(m, teamKey, fallbackTarget) {
  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  if (Array.isArray(m?.[stateKey]) && m[stateKey].length) {
    return m[stateKey].filter(Boolean).length
  }
  const hitsTaken = teamKey === 'team1' ? safeNum(m?.cups_team2) : safeNum(m?.cups_team1)
  return Math.max(0, safeNum(fallbackTarget) - hitsTaken)
}

function createKoOvertimeAllocation(teamName, players, total, extra = {}) {
  return {
    mode: 'overtime_credit',
    shooterTeamName: teamName,
    p1: players.p1,
    p2: players.p2,
    bonusCupCount: total,
    bonusP1: players.p1 && !players.p2 ? total : 0,
    bonusP2: players.p2 && !players.p1 ? total : 0,
    ...extra,
  }
}

function getKoOvertimeAssignedCups() {
  const pending = pendingKoShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return 0
  return Number(pending.bonusP1 || 0) + Number(pending.bonusP2 || 0)
}

function getKoOvertimeRemainingCups() {
  const pending = pendingKoShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return 0
  return Math.max(0, Number(pending.bonusCupCount || 0) - getKoOvertimeAssignedCups())
}

function isKoOvertimeAllocationComplete() {
  const pending = pendingKoShooter.value
  return !!pending && pending.mode === 'overtime_credit' && getKoOvertimeAssignedCups() > 0 && getKoOvertimeRemainingCups() === 0
}

function adjustKoOvertimeAllocation(slot, delta) {
  const pending = pendingKoShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return
  const key = slot === 'p2' ? 'bonusP2' : 'bonusP1'
  const current = Number(pending[key] || 0)
  if (delta < 0 && current <= 0) return
  if (delta > 0 && getKoOvertimeRemainingCups() <= 0) return
  pending[key] = Math.max(0, current + delta)
}

function buildKoOvertimeAllocations() {
  const pending = pendingKoShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return []
  const allocations = []
  if (pending.p1 && Number(pending.bonusP1 || 0) > 0) {
    allocations.push({ player_name: pending.p1, count: Number(pending.bonusP1) })
  }
  if (pending.p2 && Number(pending.bonusP2 || 0) > 0) {
    allocations.push({ player_name: pending.p2, count: Number(pending.bonusP2) })
  }
  return allocations
}

function onKoCupHit({ matchId, teamKey, cupIndex }) {
  const { rIdx, mIdx, m } = _findKoMatch(matchId)
  if (!m) return

  // Schütze ist das Team das NICHT getroffen wurde (also das andere Team)
  const shooterTeamKey = teamKey === 'team1' ? 'team2' : 'team1'
  const shooterTeamName = m[shooterTeamKey]

  const players = resolveKoTeamPlayers(shooterTeamName)

  if (players.p1 || players.p2) {
    pendingKoShooter.value = {
      mode: 'cup_hit',
      matchId, rIdx, mIdx, teamKey, cupIndex,
      shooterTeamName,
      p1: players.p1,
      p2: players.p2,
    }
    selectedKoPlayer.value = null
    return
  }

  _doKoCupHit(matchId, rIdx, mIdx, teamKey, cupIndex, null)
}

function _doKoCupHit(matchId, rIdx, mIdx, teamKey, cupIndex, shooterName) {
  const m = roundsLocal[rIdx]?.matches?.[mIdx]
  if (!m) return
  const cupsTarget = cupsTargetForRound(rIdx)
  const shooterTeamKey = teamKey === 'team1' ? 'team2' : 'team1'
  const shooterTeamName = m[shooterTeamKey]

  // stateKey  = physical cups of the team whose cup was hit (they lose a cup)
  // scoreKey  = score counter of the OTHER team (they gain a point)
  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  const scoreKey = teamKey === 'team1' ? 'cups_team2' : 'cups_team1'  // opponent scores

  if (!Array.isArray(m[stateKey]) || m[stateKey].length !== cupsTarget) {
    // Init from opponent's score (how many cups of this team were already hit)
    const existingHits = teamKey === 'team1' ? (m.cups_team2 || 0) : (m.cups_team1 || 0)
    m[stateKey] = normalizeKoStateArray(m[stateKey], cupsTarget, existingHits, !!m.is_overtime)
  }
  if (!m[stateKey][cupIndex]) return  // already hit

  m[stateKey][cupIndex] = false
  m[scoreKey] = clampInt(safeNum(m[scoreKey]) + 1, 0, cupsTarget + (m.is_overtime ? 3 : 0))

  const hKey = `${matchId}:${teamKey}`
  if (!koUndoHistory.value.has(hKey)) koUndoHistory.value.set(hKey, [])
  koUndoHistory.value.get(hKey).push(cupIndex)

  // All cups hit → conclusion dialog (not immediate winner)
  const allHit = m[stateKey].every(v => !v)
  if (allHit) {
    const step = m.is_overtime ? 'END_QUERY' : 'NACHWURF'
    pendingKoConclusion.value = { matchId, rIdx, mIdx, teamKey, step, history: [step] }
    saveSingleKoMatch(rIdx, mIdx, m, shooterName && shooterTeamName ? {
      action_type: 'cup_hit',
      team_key: teamKey,
      player_name: shooterName,
      team_name: shooterTeamName,
      credit_count: 1,
    } : null)
    return
  }

  saveSingleKoMatch(rIdx, mIdx, m, shooterName && shooterTeamName ? {
    action_type: 'cup_hit',
    team_key: teamKey,
    player_name: shooterName,
    team_name: shooterTeamName,
    credit_count: 1,
  } : null)
}

function selectKoShooter(playerName) {
  selectedKoPlayer.value = playerName
}

function confirmKoShooter() {
  if (!pendingKoShooter.value) return
  const { mode, matchId, rIdx, mIdx, teamKey, cupIndex, shooterTeamName, bonusCupCount } = pendingKoShooter.value
  if (mode !== 'overtime_credit' && !selectedKoPlayer.value) return
  const playerName = selectedKoPlayer.value
  const allocations = mode === 'overtime_credit' ? buildKoOvertimeAllocations() : []
  if (mode === 'overtime_credit' && (!allocations.length || !isKoOvertimeAllocationComplete())) return
  pendingKoShooter.value = null
  selectedKoPlayer.value = null
  if (mode === 'overtime_credit') {
    applyKoOvertime(rIdx, mIdx, {
      teamName: shooterTeamName,
      teamKey,
      creditCount: bonusCupCount,
      allocations,
    })
    return
  }
  _doKoCupHit(matchId, rIdx, mIdx, teamKey, cupIndex, playerName)
}

function cancelKoShooter() {
  pendingKoShooter.value = null
  selectedKoPlayer.value = null
}

/* Spielabschluss-Dialog */
function conclusionKoStep(step) {
  if (!pendingKoConclusion.value) return
  const h = [...(pendingKoConclusion.value.history || [])]
  h.push(step)
  pendingKoConclusion.value = { ...pendingKoConclusion.value, step, history: h }
}

function conclusionKoBack() {
  if (!pendingKoConclusion.value) return
  const h = [...(pendingKoConclusion.value.history || [])]
  if (h.length <= 1) return
  h.pop()
  pendingKoConclusion.value = { ...pendingKoConclusion.value, step: h[h.length - 1], history: h }
}

function conclusionKoOvertime() {
  if (!pendingKoConclusion.value) return
  const { rIdx, mIdx, teamKey } = pendingKoConclusion.value
  const m = roundsLocal[rIdx]?.matches?.[mIdx]
  if (!m) return
  const overtimeTeamKey = teamKey
  const overtimeTeamName = m[overtimeTeamKey]
  const opponentTeamKey = overtimeTeamKey === 'team1' ? 'team2' : 'team1'
  const remainingOpponentCups = getKoStandingCups(m, opponentTeamKey, cupsTargetForRound(rIdx))

  if (remainingOpponentCups > 0) {
    const players = resolveKoTeamPlayers(overtimeTeamName)
    if (players.p1 || players.p2) {
      pendingKoShooter.value = createKoOvertimeAllocation(overtimeTeamName, players, remainingOpponentCups, {
        matchId: `${rIdx}:${mIdx}`,
        rIdx,
        mIdx,
      })
      selectedKoPlayer.value = null
      return
    }
  }

  applyKoOvertime(rIdx, mIdx, {
    teamName: overtimeTeamName,
    teamKey: overtimeTeamKey,
    creditCount: remainingOpponentCups,
  })
}

function applyKoOvertime(rIdx, mIdx, creditInfo = null) {
  const m = roundsLocal[rIdx]?.matches?.[mIdx]
  if (!m) return
  if (creditInfo?.creditCount > 0) {
    const scoreField = creditInfo.teamKey === 'team1' ? 'cups_team1' : 'cups_team2'
    m[scoreField] = clampInt(
      safeNum(m[scoreField]) + creditInfo.creditCount,
      0,
      cupsTargetForRound(rIdx)
    )
  }
  // Verlängerung: beide Teams bekommen 3 frische Becher
  const cupsTarget = cupsTargetForRound(rIdx)
  const overtimeState = buildFrontOvertimeState(cupsTarget)
  m.cups_state_team1 = [...overtimeState]
  m.cups_state_team2 = [...overtimeState]
  m.is_overtime = true
  m.winner = null
  pendingKoConclusion.value = null
  // Clear undo history for this match (overtime resets)
  const mid = `${rIdx}:${mIdx}`
  koUndoHistory.value.delete(`${mid}:team1`)
  koUndoHistory.value.delete(`${mid}:team2`)
  saveSingleKoMatch(rIdx, mIdx, m, creditInfo?.teamName && Array.isArray(creditInfo?.allocations) && creditInfo.allocations.length ? {
    action_type: 'overtime_credit',
    team_name: creditInfo.teamName,
    credit_count: creditInfo.creditCount,
    credit_allocations: creditInfo.allocations,
  } : null)
}

function finishKoConclusion(confirm) {
  if (!pendingKoConclusion.value) return
  if (!confirm) {
    pendingKoConclusion.value = null
    return
  }
  const { rIdx, mIdx, teamKey } = pendingKoConclusion.value
  const m = roundsLocal[rIdx]?.matches?.[mIdx]
  if (!m) return
  // teamKey = team whose cups were all hit (the loser); winner is the OTHER team
  m.winner = teamKey === 'team1' ? m.team2 : m.team1
  m.status = 'done'
  pendingKoConclusion.value = null
  recalcPropagation(rIdx)
  saveSingleKoMatch(rIdx, mIdx, m)
}

function onKoUndo({ matchId, teamKey }) {
  // If there's a pending conclusion for this match, just cancel it
  if (pendingKoConclusion.value?.matchId === matchId) {
    pendingKoConclusion.value = null
    return
  }

  const { rIdx, mIdx, m } = _findKoMatch(matchId)
  if (!m) return
  const hKey = `${matchId}:${teamKey}`
  const history = koUndoHistory.value.get(hKey) || []
  if (!history.length) return

  const lastIdx = history.pop()
  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  const scoreKey = teamKey === 'team1' ? 'cups_team2' : 'cups_team1'  // opponent score

  if (Array.isArray(m[stateKey]) && lastIdx < m[stateKey].length) {
    m[stateKey][lastIdx] = true
    m[scoreKey] = clampInt(safeNum(m[scoreKey]) - 1, 0, cupsTargetForRound(rIdx) + (m.is_overtime ? 3 : 0))
  }
  m.winner = null
  recalcPropagation(rIdx)
  saveSingleKoMatch(rIdx, mIdx, m, {
    action_type: 'undo',
    team_key: teamKey,
    undo_count: 1,
  })
}

function onKoRerack({ matchId, teamKey, newState }) {
  const { rIdx, mIdx, m } = _findKoMatch(matchId)
  if (!m) return
  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  m[stateKey] = [...newState]
  m[`rerack_used_${teamKey}`] = true
  saveSingleKoMatch(rIdx, mIdx, m)
}

/* Computed Helpers */
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
 * - Finale: 10 Becher, wenn finaleWith10Cups = true
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

  if (isFinal && finaleWith10Cups.value) {
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

function emptyMatch() {
  return {
    team1: null, team2: null, winner: null,
    table_no: null,
    cups_team1: 0, cups_team2: 0,
    cups_state_team1: null, cups_state_team2: null,
    is_overtime: false,
    rerack_used_team1: false, rerack_used_team2: false,
  }
}

function buildEmptyRound(matchesCount) {
  return {
    bracket_type: 'main',
    round_name: '',
    matches: Array.from({ length: matchesCount }, emptyMatch)
  }
}

function buildPlacementRound() {
  return {
    bracket_type: 'placement',
    round_name: 'Spiel um Platz 3',
    matches: [emptyMatch()]
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
  if (isKoMatchStartedLocal(match)) return
  const teamsChanged = match.team1 !== newTeam1 || match.team2 !== newTeam2
  if (!teamsChanged) return
  match.team1 = newTeam1
  match.team2 = newTeam2
  resetKoMatchProgress(match)
}

function propagateAll(rounds) {
  for (let r = 0; r < rounds.length - 1; r++) {
    const cur = rounds[r]
    const nxt = rounds[r + 1]
    if (!cur || !nxt) continue
    if (cur.bracket_type !== 'main' || nxt.bracket_type !== 'main') continue
    syncNextRoundFromCurrent(cur, nxt)
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
      ...emptyMatch(),
      team1: p[0],
      team2: p[1],
      winner: autoWinner(p[0], p[1]),
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
  activeMainRoundIndex.value = 0
  activeStageKind.value = 'main'
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
    syncNextRoundFromCurrent(cur, nxt)
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
function applyKoPhaseSnapshot(koPhaseSnapshot = {}, tournamentSnapshot = null) {
  const t = tournamentSnapshot ?? {}
  const parsedBaseCups = Number(t.cupsPerGame ?? t.cups_per_game)
  if (Number.isFinite(parsedBaseCups) && parsedBaseCups > 0) {
    baseCupsPerGame.value = parsedBaseCups
  }
  if (Object.prototype.hasOwnProperty.call(t, 'finaleWith10Cups') || Object.prototype.hasOwnProperty.call(t, 'finale_with_10_cups')) {
    finaleWith10Cups.value = !!(t.finaleWith10Cups ?? t.finale_with_10_cups)
  }
  const tc = Number(t.tableCount ?? t.table_count)
  if (Number.isFinite(tc) && tc > 0) tableCount.value = tc

  const serverRounds = koPhaseSnapshot?.rounds || []
  const serverActiveMainRoundIndex = koPhaseSnapshot?.active_main_round_index ?? koPhaseSnapshot?.activeMainRoundIndex ?? null
  const serverActiveStageKind = koPhaseSnapshot?.active_stage_kind ?? koPhaseSnapshot?.activeStageKind ?? null

  if (serverRounds.length > 0) {
    let all = serverRounds.map(r => ({
      bracket_type: r.bracket_type || 'main',
      round_name: r.round_name || '',
      matches: (r.matches || []).map(m => {
        const team1 = m.team1 ?? null
        const team2 = m.team2 ?? null
        const cups1 = +m.cups_team1 || 0
        const cups2 = +m.cups_team2 || 0
        const status = m.status ?? (m.winner ? 'done' : 'pending')
        const winner =
          (m.winner === team1 || m.winner === team2)
            ? m.winner
            : (status === 'done' && team1 && team2 && cups1 !== cups2
              ? (cups1 > cups2 ? team1 : team2)
              : null)

        return {
          id: m.id ?? null,
          ko_match_index: Number.isInteger(Number(m.ko_match_index)) ? Number(m.ko_match_index) : null,
          team1,
          team2,
          winner,
          status,
          table_no: Number.isFinite(Number(m.table_no)) && Number(m.table_no) > 0 ? Number(m.table_no) : null,
          cups_team1: cups1,
          cups_team2: cups2,
          cups_state_team1: Array.isArray(m.cups_state_team1) && m.cups_state_team1.length ? m.cups_state_team1 : null,
          cups_state_team2: Array.isArray(m.cups_state_team2) && m.cups_state_team2.length ? m.cups_state_team2 : null,
          is_overtime: !!m.is_overtime,
          rerack_used_team1: false,
          rerack_used_team2: false,
        }
      })
    }))

    let mainRounds = all.filter(r => r.bracket_type !== 'placement')
    let placementRounds = all.filter(r => r.bracket_type === 'placement')

    const derivedSize = Math.max(2, (mainRounds[0]?.matches?.length || 1) * 2)
    const size = props.koSize || derivedSize
    const totalRounds = Math.max(1, Math.log2(size) | 0)
    const paddedMainRounds = []
    for (let roundIdx = 0; roundIdx < totalRounds; roundIdx++) {
      const expectedMatchCount = Math.max(1, size >> (roundIdx + 1))
      const existingRound = mainRounds[roundIdx]
      const existingMatches = existingRound?.matches || []
      const targetMatchCount = Math.max(expectedMatchCount, existingMatches.length)
      const matches = existingMatches.slice()

      while (matches.length < targetMatchCount) {
        matches.push(emptyMatch())
      }

      paddedMainRounds.push({
        ...(existingRound || buildEmptyRound(targetMatchCount)),
        bracket_type: 'main',
        round_name: roundNameFor(totalRounds, roundIdx),
        matches,
      })
    }

    mainRounds = paddedMainRounds

    if (!placementRounds.length && size >= 4) {
      placementRounds.push(buildPlacementRound())
    }

    const rounds = [...mainRounds, ...placementRounds]
    propagateAll(rounds)
    applyRounds(rounds)
    const parsedActiveRoundIndex = Number(serverActiveMainRoundIndex)
    activeMainRoundIndex.value = Number.isInteger(parsedActiveRoundIndex)
      ? parsedActiveRoundIndex
      : getKoStageMeta(roundsLocal, null).activeMainRoundIndex
    activeStageKind.value = serverActiveStageKind ?? getKoStageMeta(roundsLocal, activeMainRoundIndex.value).activeStageKind
    return true
  }

  if (roundsLocal.length === 0 && initialTeams.value.length > 0) {
    seedBracket()
    return true
  }
  return false
}

async function loadFromServer() {
  loading.value = true
  try {
    const [resBracket, resData] = await Promise.all([
      fetch(`${API}/tournaments/${props.tournamentId}/load-ko-bracket`).catch(() => null),
      fetch(`${API}/tournaments/${props.tournamentId}/load-all-data`).catch(() => null)
    ])

    let tournamentSnapshot = null
    if (resData && resData.ok) {
      const tData = await resData.json()
      tournamentSnapshot = tData?.tournament ?? null
    }
    _tableCountLoading.value = false

    let koPhaseSnapshot = null
    if (resBracket && resBracket.ok) {
      const bracketData = await resBracket.json().catch(() => null)
      koPhaseSnapshot = bracketData
    }
    applyKoPhaseSnapshot(koPhaseSnapshot || {}, tournamentSnapshot)
  } catch (e) {
    console.error(e)
    if (roundsLocal.length === 0 && initialTeams.value.length > 0) seedBracket()
  } finally {
    loading.value = false
    _tableCountLoading.value = false
  }
}

async function saveToServer() {
  loading.value = true
  try {
    const payload = {
      rounds: roundsLocal,
      active_main_round_index: activeMainRoundIndex.value,
      active_stage_kind: activeStageKind.value,
    }
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

async function startNextKoRound() {
  if (!canStartNextKoRound.value) return
  loading.value = true
  try {
    const mainInfos = getKoMainRoundInfos(roundsLocal)
    const nextMainRoundPayload = buildNextMainRoundForRelease(activeMainRoundIndex.value + 1)
    const placementRoundPayload = (activeMainRoundIndex.value + 1 === mainInfos.length - 1)
      ? buildPlacementRoundForRelease()
      : null
    const res = await fetch(`${API}/tournaments/${props.tournamentId}/start-ko-next-round`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        active_main_round_index: activeMainRoundIndex.value,
        active_stage_kind: activeStageKind.value,
        next_main_round: nextMainRoundPayload,
        placement_round: placementRoundPayload,
      }),
    })
    const data = await res.json().catch(() => null)
    if (!res.ok) throw new Error(data?.error || 'start next ko round failed')
    const nextIndex = Number(data?.active_main_round_index ?? data?.activeMainRoundIndex)
    if (Number.isInteger(nextIndex)) activeMainRoundIndex.value = nextIndex
    activeStageKind.value = data?.active_stage_kind ?? data?.activeStageKind ?? activeStageKind.value
    store.applyState({ ko_phase: data || {} })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function saveSingleKoMatch(rIdx, mIdx, m, eventData = null) {
  try {
    const tableNo = Number.isFinite(Number(m.table_no)) && Number(m.table_no) > 0
      ? Number(m.table_no)
      : (koTableMap.value.get(`${rIdx}:${mIdx}`) ?? null)
    m.table_no = tableNo
    const body = {
      match_id: m.id ?? null,
      round_index: rIdx,
      match_index: mIdx,
      round_name: roundsLocal[rIdx]?.round_name || '',
      team1: m.team1, team2: m.team2, winner: m.winner,
      table_no: tableNo,
      is_overtime: !!m.is_overtime,
      cups_team1: m.cups_team1, cups_team2: m.cups_team2,
      cups_state_team1: Array.isArray(m.cups_state_team1) ? m.cups_state_team1 : null,
      cups_state_team2: Array.isArray(m.cups_state_team2) ? m.cups_state_team2 : null,
      shooter: eventData?.player_name || null,
      shooter_team: eventData?.team_name || null,
      event_data: eventData || null,
    }
    const res = await fetch(`${API}/tournaments/${props.tournamentId}/ko-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    if (!res.ok && res.status !== 404) throw new Error('Failed single save')
    if (res.status === 404) await saveToServer()
    const data = res.ok ? await res.json().catch(() => null) : null
    if (data && Object.prototype.hasOwnProperty.call(data, 'top_players')) {
      store.topPlayers = data.top_players || []
    }
  } catch (e) {
    console.error(e)
  }
}

function applyRounds(newRounds) {
  roundsLocal.splice(0, roundsLocal.length, ...(newRounds ?? []))
}

watch(() => store.koPhase, (newKoPhase) => {
  if (pendingKoShooter.value || pendingKoConclusion.value) return
  if (!newKoPhase?.rounds) return
  applyKoPhaseSnapshot(newKoPhase, store.tournament || null)
}, { deep: true })

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

/* Live KO tables section */
.ko-live-section {
  max-width: 1250px;
  margin-left: auto;
  margin-right: auto;
}
.ko-live-header { }
.ko-live-badge {
  font-size: 0.85rem;
  padding: 0.4em 0.8em;
}
.ko-live-tables {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  justify-content: flex-start;
}
.ko-live-table-wrap {
  flex: 0 0 auto;
}
.ko-live-table-label {
  text-align: center;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.ko-shooter-overlay {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px solid #ffc107 !important;
}

.ko-credit-card {
  min-width: 180px;
  padding: 0.85rem 1rem;
  border: 1px solid rgba(255, 193, 7, 0.35);
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.04);
}

.ko-credit-count {
  min-width: 3.5rem;
}

.ko-tab-root {
  width: 100%;
}

.ko-section-head {
  font-size: 0.8rem;
  font-weight: 700;
  color: #f8f9fa;
}

.ko-bracket-wrap {
  width: 100%;
  overflow: visible;
}

.ko-manual-panel {
  border-top: 1px solid rgba(108, 117, 125, 0.35);
  padding-top: 0.75rem;
}

.ko-manual-panel__summary {
  cursor: pointer;
  list-style: none;
}

.ko-manual-panel__body {
  background: rgba(17, 24, 39, 0.82) !important;
}
</style>
