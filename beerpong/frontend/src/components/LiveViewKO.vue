<template>
  <div class="lvko-shell">

    <!-- Shared phase bar -->
    <div class="lvko-phase-bar">
      <span class="badge" :class="phase === 'ko_preview' ? 'bg-warning text-dark lvko-phase-badge' : 'bg-danger lvko-phase-badge'">
        {{ phase === 'ko_preview' ? '🏁 K.O.-Vorschau' : '🏆 K.O.-Phase' }}
      </span>
      <span class="lvko-tournament-name">{{ tournament?.name }}</span>
      <span class="badge ms-auto" :class="wsConnected ? 'bg-success' : 'bg-secondary'">
        {{ wsConnected ? '● Live' : '○ Offline' }}
      </span>
    </div>

    <!-- KO Preview: wide bracket + narrow QR side -->
    <template v-if="phase === 'ko_preview'">
      <div class="lvko-preview-layout">
        <div class="lvko-bracket-scroll lvko-bracket-main">
          <div v-if="previewSlots.length" class="lvko-preview-wrap">
            <KnockoutPreviewTree :slots="previewSlots" :ko-size="previewKoSize" :constrain-to-height="true" />
          </div>
          <div v-else class="lvko-empty">
            <div class="spinner-border text-secondary mb-3" role="status"></div>
            <div class="text-secondary">K.O.-Vorschau wird geladen…</div>
          </div>
        </div>
        <div class="lvko-side">
          <div class="card bg-black border-secondary lvko-qr-card text-center">
            <div class="card-body p-3 d-flex flex-column align-items-center justify-content-center gap-1">
              <div class="text-secondary small text-uppercase" style="letter-spacing:.1em">Mobile Ansicht</div>
              <canvas ref="qrCanvas" class="lvko-qr-canvas"></canvas>
              <small class="text-secondary lvko-qr-url">{{ mobileUrl }}</small>
            </div>
          </div>
          <div class="text-center mt-2">
            <button class="btn btn-outline-secondary btn-sm" @click="$emit('deselect')">Anderes Turnier</button>
          </div>
        </div>
      </div>
    </template>

    <!-- KO Phase: live tables prominent at top, bracket + QR below -->
    <template v-else-if="phase === 'ko'">
      <!-- Live tables row -->
      <div class="lvko-tables-row">
        <template v-if="liveMatchCards.length">
          <LiveTable3D
            v-for="(m, i) in liveMatchCards"
            :key="m.id ?? i"
            :match="m"
            :cups-per-game="m.match_cups_per_game ?? cupsPerGame"
            :table-label="`Tisch ${m.table_no} • ${m.round_name}`"
            show-score beam
          />
        </template>
        <div v-else class="lvko-tables-empty text-secondary small">
          <div class="spinner-border spinner-border-sm me-2" role="status"></div>
          Warte auf Spiele…
        </div>
      </div>

      <!-- Bottom row: bracket + QR -->
      <div class="lvko-bottom-row">
        <div class="lvko-bracket-scroll lvko-bracket-bottom">
          <div v-if="koRounds.length" class="lvko-results-wrap">
            <KnockoutResultsTree
              :rounds="koRounds"
              :active-match-ids="activeMatchIds"
              :constrain-to-height="true"
            />
          </div>
          <div v-else class="lvko-empty">
            <div class="spinner-border text-secondary mb-3" role="status"></div>
            <div class="text-secondary">K.O.-Bracket wird geladen…</div>
          </div>
        </div>
        <div class="lvko-side">
          <div class="card bg-black border-secondary lvko-qr-card text-center">
            <div class="card-body p-3 d-flex flex-column align-items-center justify-content-center gap-1">
              <div class="text-secondary small text-uppercase" style="letter-spacing:.1em">Mobile Ansicht</div>
              <canvas ref="qrCanvas" class="lvko-qr-canvas"></canvas>
              <small class="text-secondary lvko-qr-url">{{ mobileUrl }}</small>
            </div>
          </div>
          <div class="text-center mt-2">
            <button class="btn btn-outline-secondary btn-sm" @click="$emit('deselect')">Anderes Turnier</button>
          </div>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import QRCode from 'qrcode'
import { useTournamentStore } from '../stores/tournament.js'
import KnockoutPreviewTree from './KnockoutPreviewTree.vue'
import KnockoutResultsTree from './KnockoutResultsTree.vue'
import LiveTable3D from './LiveTable3D.vue'
import { getKOActiveMatches, makeCupsStateFromCount } from '../utils/tableAssignments.js'
import { inferKoMatchCupsTarget, normalizeKoRoundsForDisplay } from '../utils/koDisplay.js'

defineEmits(['deselect'])

const store = useTournamentStore()

const tournament  = computed(() => store.tournament)
const phase       = computed(() => tournament.value?.current_phase ?? tournament.value?.currentPhase ?? 'group')
const wsConnected = computed(() => store.wsConnected)
const koRounds    = computed(() => normalizeKoRoundsForDisplay(store.koPhase?.rounds ?? []))
const koPreview   = computed(() => store.koPreview ?? {})
const groupStandings = computed(() => store.groupStandings ?? {})
const playin = computed(() => store.playin ?? {})
const tableCount  = computed(() => Number(tournament.value?.tableCount ?? tournament.value?.table_count ?? 2) || 2)
const cupsPerGame = computed(() => Number(tournament.value?.cupsPerGame ?? tournament.value?.cups_per_game ?? 6) || 6)
const finaleWith10Cups = computed(() => !!(tournament.value?.finaleWith10Cups ?? tournament.value?.finale_with_10_cups))
const activeKoMainRoundIndex = computed(() =>
  store.koPhase?.active_main_round_index ?? store.koPhase?.activeMainRoundIndex ?? null
)
const activeKoStageKind = computed(() =>
  store.koPhase?.active_stage_kind ?? store.koPhase?.activeStageKind ?? null
)

const activeKOMatches = computed(() =>
  getKOActiveMatches(koRounds.value, tableCount.value, activeKoMainRoundIndex.value, activeKoStageKind.value)
)
const activeMatchIds  = computed(() => new Set(activeKOMatches.value.map(m => m.id).filter(id => id != null)))
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
const previewSlots    = computed(() => {
  const persisted = Array.isArray(koPreview.value?.slots) ? koPreview.value.slots : []
  if (persisted.length > 0) return persisted

  const fromPlayin = playin.value?.direct_qualified_slots
  if (Array.isArray(fromPlayin) && fromPlayin.length > 0) {
    const playinMatches = playin.value?.playin_matches ?? playin.value?.matches ?? []
    return [
      ...fromPlayin,
      ...playinMatches.map((m, idx) => ({
        id: `live-playin-${idx}`,
        sourceLabel: `Sieger Play-In ${idx + 1}`,
        teamName: m?.winner || '',
      })),
    ]
  }

  const winners = []
  const runnersUp = []
  for (const [groupName, rows] of Object.entries(groupStandings.value || {})) {
    const label = normalizeGroupLabel(groupName)
    if (rows?.[0]?.name) winners.push({ id: `live-${groupName}-1`, sourceLabel: `Sieger ${label}`, teamName: rows[0].name })
    if (rows?.[1]?.name) runnersUp.push({ id: `live-${groupName}-2`, sourceLabel: `2. ${label}`, teamName: rows[1].name })
  }

  const derived = []
  for (let i = 0; i < winners.length; i++) {
    derived.push(winners[i])
    const mirroredRunner = runnersUp[runnersUp.length - 1 - i]
    if (mirroredRunner) derived.push(mirroredRunner)
  }

  const playinMatches = playin.value?.playin_matches ?? playin.value?.matches ?? []
  playinMatches.forEach((m, idx) => {
    derived.push({
      id: `live-playin-${idx}`,
      sourceLabel: `Sieger Play-In ${idx + 1}`,
      teamName: m?.winner || '',
    })
  })
  return derived
})
const previewKoSize   = computed(() => {
  const fromStore = Number(koPreview.value?.ko_size ?? koPreview.value?.koSize ?? playin.value?.ko_size ?? 0)
  if (fromStore > 0) return fromStore
  let p = 1
  const n = Math.max(4, previewSlots.value.length || 0)
  while (p < n) p *= 2
  return p
})
const liveMatchCards  = computed(() =>
  activeKOMatches.value.map(m => ({
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
)

const qrCanvas = ref(null)
const vpWidth  = ref(typeof window !== 'undefined' ? window.innerWidth  : 1920)
const vpHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 1080)

const qrSize = computed(() =>
  Math.round(Math.max(120, Math.min(260, vpWidth.value * 0.14, vpHeight.value * 0.22)))
)

const mobileUrl = computed(() => {
  const t = tournament.value
  if (!t?.mobileAccessToken || !t?.id) return ''
  const base = window.location.origin + window.location.pathname
  return `${base}#/mobile?token=${t.mobileAccessToken}&id=${t.id}`
})

async function drawQR(url) {
  if (!url || !qrCanvas.value) return
  await nextTick()
  try {
    await QRCode.toCanvas(qrCanvas.value, url, {
      width: qrSize.value,
      color: { dark: '#ffffff', light: '#000000' },
    })
  } catch (e) { console.error('QR error', e) }
}

watch(mobileUrl, drawQR)
watch(qrSize, () => drawQR(mobileUrl.value))

function onResize() {
  vpWidth.value  = window.innerWidth
  vpHeight.value = window.innerHeight
}

function normalizeGroupLabel(groupName) {
  const raw = String(groupName ?? '').trim()
  if (!raw) return 'Gruppe'
  return /^gruppe\b/i.test(raw) ? raw : `Gruppe ${raw}`
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  drawQR(mobileUrl.value)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
/* ── Root: fills the flex column that LiveView gives us ──────────────────── */
.lvko-shell {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: clamp(8px, 1vh, 14px);
  padding: clamp(8px, 1vh, 14px) clamp(12px, 1.4vw, 20px);
  overflow: hidden;
}

/* ── Phase bar (shared) ──────────────────────────────────────────────────── */
.lvko-phase-bar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.lvko-phase-badge {
  font-size: clamp(0.78rem, 1vw, 0.95rem);
  padding: 0.4em 0.75em;
}

.lvko-tournament-name {
  color: #fff;
  font-size: clamp(1rem, 1.8vw, 1.6rem);
  font-weight: 800;
  letter-spacing: 0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* ── KO Preview layout: wide bracket + narrow QR ────────────────────────── */
.lvko-preview-layout {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  gap: clamp(10px, 1.2vw, 18px);
}

/* ── KO Phase: tables at top (prominent) ────────────────────────────────── */
.lvko-tables-row {
  flex: 0 0 auto;
  display: flex;
  flex-direction: row;
  gap: clamp(15px, 2vw, 30px);
  overflow: hidden;
  padding: 8px 0;
  align-items: center;
  justify-content: center;
  min-height: clamp(240px, 34vh, 480px);
}

/* Compact the 3D tables in the live strip so the bracket gets more space */
.lvko-tables-row :deep(.beer-table--beam) {
  --tw:    clamp(110px, min(10vw, 12vh), 180px);
  --ratio: 2.6;
  --tilt:  28deg;
  --nf:    clamp(0.85rem, 1.0vw, 1.15rem);
  --labelf: clamp(0.65rem, 0.78vw, 0.85rem);
}

.lvko-tables-empty {
  display: flex;
  align-items: center;
  padding: 1rem 0;
}

/* ── Bottom row: bracket + QR ───────────────────────────────────────────── */
.lvko-bottom-row {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  gap: clamp(10px, 1.2vw, 18px);
}

/* ── Bracket scroll (shared, different flex in each context) ─────────────── */
.lvko-bracket-scroll {
  overflow: auto;
  padding-bottom: 4px;
}

.lvko-bracket-main {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
}

.lvko-bracket-bottom {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
}

/* Fill the scroll container — zoom inside the bracket handles sizing */
.lvko-preview-wrap,
.lvko-results-wrap {
  width: 100%;
  height: 100%;
  padding: 0 6px 8px;
  box-sizing: border-box;
}

/* Propagate container height into the bracket component so it can
   measure available height and scale to fit both axes */
.lvko-results-wrap :deep(.bracket-tree),
.lvko-results-wrap :deep(.bracket-tree__scroll),
.lvko-preview-wrap :deep(.bracket-tree),
.lvko-preview-wrap :deep(.bracket-tree__scroll) {
  height: 100%;
}

.lvko-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
}

/* ── Side column: QR + deselect button ──────────────────────────────────── */
.lvko-side {
  flex: 0 0 clamp(120px, 10vw, 175px);
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lvko-qr-card {
  flex: 0 0 auto;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(4,4,4,0.98) 0%, rgba(14,18,26,0.98) 100%) !important;
  border-color: rgba(255,255,255,0.16) !important;
}

.lvko-qr-canvas {
  width: 100%;
  height: auto;
  max-width: min(15vh, 12vw, 140px);
  aspect-ratio: 1 / 1;
  object-fit: contain;
  border-radius: 8px;
}

.lvko-qr-url {
  font-size: 0.35rem;
  word-break: break-all;
  overflow-wrap: anywhere;
  color: rgba(255,255,255,0.18) !important;
  line-height: 1.1;
  display: block;
  max-width: 100%;
}

@media (max-height: 800px) {
  .lvko-qr-canvas { max-width: min(12vh, 10vw, 110px); }
  .lvko-side { gap: 6px; }
}
</style>
