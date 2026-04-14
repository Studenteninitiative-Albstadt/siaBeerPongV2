<template>
  <div class="lvko-shell">

    <!-- Bracket area — fills all remaining space -->
    <div class="lvko-main">
      <div class="lvko-phase-bar">
        <span class="badge" :class="phase === 'ko_preview' ? 'bg-warning text-dark lvko-phase-badge' : 'bg-danger lvko-phase-badge'">
          {{ phase === 'ko_preview' ? '🏁 K.O.-Vorschau' : '🏆 K.O.-Phase' }}
        </span>
        <span class="lvko-tournament-name">{{ tournament?.name }}</span>
        <span class="badge ms-auto" :class="wsConnected ? 'bg-success' : 'bg-secondary'">
          {{ wsConnected ? '● Live' : '○ Offline' }}
        </span>
      </div>

      <div class="lvko-bracket-scroll">
        <KnockoutBracket
          v-if="phase === 'ko' && koRounds.length"
          :rounds="koRounds"
          :readonly="true"
          :interactive="false"
          :active-match-ids="activeMatchIds"
        />
        <div v-else-if="phase === 'ko_preview' && previewSlots.length" class="lvko-preview-wrap">
          <KnockoutPreviewTree
            :slots="previewSlots"
            :ko-size="previewKoSize"
          />
        </div>
        <div v-else class="lvko-empty">
          <div class="spinner-border text-secondary mb-3" role="status"></div>
          <div class="text-secondary">
            {{ phase === 'ko_preview' ? 'K.O.-Vorschau wird geladen…' : 'K.O.-Bracket wird geladen…' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Right column: live matches + QR code + deselect -->
    <div class="lvko-side">

      <!-- Live KO matches (compact) -->
      <div v-if="liveMatchCards.length" class="lvko-live-section">
        <div class="lvko-live-label">🔴 Live</div>
        <div class="lvko-live-scroll">
          <LiveTable3D
            v-for="(m, i) in liveMatchCards"
            :key="m.id ?? i"
            :match="m"
            :cups-per-game="cupsPerGame"
            :table-label="`Tisch ${m.table_no} • ${m.round_name}`"
            compact show-score beam
          />
        </div>
      </div>

      <!-- QR code -->
      <div class="card bg-black border-secondary lvko-qr-card text-center">
        <div class="card-body p-3 d-flex flex-column align-items-center justify-content-center gap-2">
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

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import QRCode from 'qrcode'
import { useTournamentStore } from '../stores/tournament.js'
import KnockoutBracket from './KnockoutBracket.vue'
import KnockoutPreviewTree from './KnockoutPreviewTree.vue'
import LiveTable3D from './LiveTable3D.vue'
import { getKOActiveMatches, makeCupsStateFromCount } from '../utils/tableAssignments.js'

defineEmits(['deselect'])

const store = useTournamentStore()

const tournament  = computed(() => store.tournament)
const phase       = computed(() => tournament.value?.current_phase ?? tournament.value?.currentPhase ?? 'group')
const wsConnected = computed(() => store.wsConnected)
const koRounds    = computed(() => store.koPhase?.rounds ?? [])
const koPreview   = computed(() => store.koPreview ?? {})
const groupStandings = computed(() => store.groupStandings ?? {})
const playin = computed(() => store.playin ?? {})
const tableCount  = computed(() => Number(tournament.value?.tableCount ?? tournament.value?.table_count ?? 2) || 2)
const cupsPerGame = computed(() => Number(tournament.value?.cupsPerGame ?? tournament.value?.cups_per_game ?? 6) || 6)

const activeKOMatches = computed(() => getKOActiveMatches(koRounds.value, tableCount.value))
const activeMatchIds  = computed(() => new Set(activeKOMatches.value.map(m => m.id).filter(id => id != null)))
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
    cups_state_team1: makeCupsStateFromCount(m.cups_team1, cupsPerGame.value),
    cups_state_team2: makeCupsStateFromCount(m.cups_team2, cupsPerGame.value),
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
  gap: clamp(10px, 1.2vw, 18px);
  padding: clamp(10px, 1.2vh, 16px) clamp(12px, 1.4vw, 20px);
  overflow: hidden;
}

/* ── Main bracket column ─────────────────────────────────────────────────── */
.lvko-main {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

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

.lvko-bracket-scroll {
  flex: 1 1 0;
  min-height: 0;
  overflow: auto;
  padding-bottom: 4px;
}

.lvko-preview-wrap {
  min-width: max-content;
  padding: 0 6px 8px;
}

.lvko-preview-wrap :deep(.bracket-tree) {
  --bracket-side-width: 170px !important;
  --bracket-center-width: 190px !important;
  --bracket-gap: 0.65rem !important;
  --bracket-padding: 0.8rem !important;
}

.lvko-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
}

/* ── Side column: live matches + QR + deselect button ───────────────────── */
.lvko-side {
  flex: 0 0 clamp(180px, 17vw, 260px);
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lvko-live-section {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.lvko-live-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #dc3545;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.lvko-live-scroll {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  max-height: 55vh;
}

.lvko-qr-card {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(4,4,4,0.98) 0%, rgba(14,18,26,0.98) 100%) !important;
  border-color: rgba(255,255,255,0.16) !important;
}

.lvko-qr-canvas {
  width: 100%;
  max-width: min(20vh, 13vw, 180px);
  aspect-ratio: 1;
}

.lvko-qr-url {
  font-size: 0.52rem;
  word-break: break-all;
  color: rgba(255,255,255,0.32) !important;
  line-height: 1.4;
}

@media (max-height: 800px) {
  .lvko-qr-canvas { max-width: min(16vh, 12vw, 150px); }
}
</style>
