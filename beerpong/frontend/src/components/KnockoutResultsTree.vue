<template>
  <div class="bracket-tree" :class="{ 'bracket-tree--compact': compact }" :style="layoutStyle">
    <div class="bracket-tree__scroll" ref="scrollRef">
      <div class="bracket-tree__layout" ref="layoutRef" :style="zoomStyle">
        <div class="bracket-tree__side bracket-tree__side--left">
          <section
            v-for="column in leftColumns"
            :key="column.id"
            class="bracket-column"
          >
            <header class="bracket-column__header">
              <span class="bracket-column__title">{{ column.name }}</span>
            </header>

            <div class="bracket-column__matches">
              <article
                v-for="match in column.matches"
                :key="match.id"
                class="bracket-match"
              >
                <div class="bracket-match__head">
                  <div class="bracket-match__label">{{ match.label }}</div>
                  <span
                    v-if="isActiveMatch(match.id)"
                    class="bracket-live-pulse"
                    aria-label="Live-Spiel"
                  ></span>
                </div>

                <div
                  class="bracket-slot"
                  :class="slotClass(match.team1)"
                >
                  <div class="bracket-slot__seed">{{ match.team1.sourceLabel }}</div>
                  <div class="bracket-slot__team">
                    {{ match.team1.metaLabel }}
                  </div>
                </div>

                <div class="bracket-match__versus">vs</div>

                <div
                  class="bracket-slot"
                  :class="slotClass(match.team2)"
                >
                  <div class="bracket-slot__seed">{{ match.team2.sourceLabel }}</div>
                  <div class="bracket-slot__team">
                    {{ match.team2.metaLabel }}
                  </div>
                </div>

                <div
                  class="bracket-match__winner"
                  :class="{ 'bracket-match__winner--hidden': !match.winner }"
                >
                  {{ match.winner ? `🏆 ${match.winner}` : '\u00A0' }}
                </div>
              </article>
            </div>
          </section>
        </div>

        <div class="bracket-tree__center">
          <section class="bracket-center-card bracket-center-card--final">
            <header class="bracket-column__header bracket-column__header--center">
              <span class="bracket-column__title bracket-column__title--final">{{ finalTitle }}</span>
            </header>
            <article class="bracket-match bracket-match--featured">
              <div class="bracket-match__head">
                <div class="bracket-match__label">{{ displayFinalMatch.label }}</div>
                <span
                  v-if="isActiveMatch(displayFinalMatch.id)"
                  class="bracket-live-pulse"
                  aria-label="Live-Spiel"
                ></span>
              </div>

              <div class="bracket-slot" :class="slotClass(displayFinalMatch.team1)">
                <div class="bracket-slot__seed">{{ displayFinalMatch.team1.sourceLabel }}</div>
                <div class="bracket-slot__team">
                  {{ displayFinalMatch.team1.metaLabel }}
                </div>
              </div>

              <div class="bracket-match__versus">vs</div>

              <div class="bracket-slot" :class="slotClass(displayFinalMatch.team2)">
                <div class="bracket-slot__seed">{{ displayFinalMatch.team2.sourceLabel }}</div>
                <div class="bracket-slot__team">
                  {{ displayFinalMatch.team2.metaLabel }}
                </div>
              </div>

              <div
                class="bracket-match__winner bracket-match__winner--gold"
                :class="{ 'bracket-match__winner--hidden': !displayFinalMatch.winner }"
              >
                {{ displayFinalMatch.winner ? `🏆 ${displayFinalMatch.winner}` : '\u00A0' }}
              </div>
            </article>
          </section>

          <section
            v-if="showThirdPlaceCard"
            class="bracket-center-card bracket-center-card--third"
          >
            <header class="bracket-column__header bracket-column__header--center">
              <span class="bracket-column__title">{{ thirdPlaceTitle }}</span>
            </header>
            <article class="bracket-match">
              <div class="bracket-match__head">
                <div class="bracket-match__label">{{ displayThirdPlaceMatch.label }}</div>
                <span
                  v-if="isActiveMatch(displayThirdPlaceMatch.id)"
                  class="bracket-live-pulse"
                  aria-label="Live-Spiel"
                ></span>
              </div>

              <div class="bracket-slot" :class="slotClass(displayThirdPlaceMatch.team1)">
                <div class="bracket-slot__seed">{{ displayThirdPlaceMatch.team1.sourceLabel }}</div>
                <div class="bracket-slot__team">
                  {{ displayThirdPlaceMatch.team1.metaLabel }}
                </div>
              </div>

              <div class="bracket-match__versus">vs</div>

              <div class="bracket-slot" :class="slotClass(displayThirdPlaceMatch.team2)">
                <div class="bracket-slot__seed">{{ displayThirdPlaceMatch.team2.sourceLabel }}</div>
                <div class="bracket-slot__team">
                  {{ displayThirdPlaceMatch.team2.metaLabel }}
                </div>
              </div>

              <div
                class="bracket-match__winner"
                :class="{ 'bracket-match__winner--hidden': !displayThirdPlaceMatch.winner }"
              >
                {{ displayThirdPlaceMatch.winner ? `🏆 ${displayThirdPlaceMatch.winner}` : '\u00A0' }}
              </div>
            </article>
          </section>
        </div>

        <div class="bracket-tree__side bracket-tree__side--right">
          <section
            v-for="column in rightColumns"
            :key="column.id"
            class="bracket-column"
          >
            <header class="bracket-column__header">
              <span class="bracket-column__title">{{ column.name }}</span>
            </header>

            <div class="bracket-column__matches">
              <article
                v-for="match in column.matches"
                :key="match.id"
                class="bracket-match"
              >
                <div class="bracket-match__head">
                  <div class="bracket-match__label">{{ match.label }}</div>
                  <span
                    v-if="isActiveMatch(match.id)"
                    class="bracket-live-pulse"
                    aria-label="Live-Spiel"
                  ></span>
                </div>

                <div
                  class="bracket-slot"
                  :class="slotClass(match.team1)"
                >
                  <div class="bracket-slot__seed">{{ match.team1.sourceLabel }}</div>
                  <div class="bracket-slot__team">
                    {{ match.team1.metaLabel }}
                  </div>
                </div>

                <div class="bracket-match__versus">vs</div>

                <div
                  class="bracket-slot"
                  :class="slotClass(match.team2)"
                >
                  <div class="bracket-slot__seed">{{ match.team2.sourceLabel }}</div>
                  <div class="bracket-slot__team">
                    {{ match.team2.metaLabel }}
                  </div>
                </div>

                <div
                  class="bracket-match__winner"
                  :class="{ 'bracket-match__winner--hidden': !match.winner }"
                >
                  {{ match.winner ? `🏆 ${match.winner}` : '\u00A0' }}
                </div>
              </article>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  rounds: { type: Array, default: () => [] },
  compact: { type: Boolean, default: true },
  finalTitle: { type: String, default: 'Finale' },
  thirdPlaceTitle: { type: String, default: 'Spiel um Platz 3' },
  activeMatchIds: { type: Object, default: null },
  constrainToHeight: { type: Boolean, default: false },
})

const mainRounds = computed(() =>
  (props.rounds || []).filter(round => round?.bracket_type !== 'placement')
)

const sideRounds = computed(() => mainRounds.value.slice(0, -1))

const leftColumns = computed(() =>
  sideRounds.value
    .map((round, roundIdx) => ({
      id: `left-${round.id ?? round.round_name ?? roundIdx}`,
      name: round.round_name || `Runde ${roundIdx + 1}`,
      matches: normalizeMatches(round.matches, round.round_name).slice(
        0,
        Math.ceil((round.matches || []).length / 2)
      ),
    }))
    .filter(column => column.matches.length)
)

const rightColumns = computed(() =>
  sideRounds.value
    .map((round, roundIdx) => ({
      id: `right-${round.id ?? round.round_name ?? roundIdx}`,
      name: round.round_name || `Runde ${roundIdx + 1}`,
      matches: normalizeMatches(round.matches, round.round_name).slice(
        Math.ceil((round.matches || []).length / 2)
      ),
    }))
    .filter(column => column.matches.length)
    .reverse()
)

const finalMatch = computed(() => {
  const lastRound = mainRounds.value[mainRounds.value.length - 1]
  return normalizeMatch(lastRound?.matches?.[0], lastRound?.round_name, 0)
})

const thirdPlaceMatch = computed(() => {
  const placementRound = (props.rounds || []).find(round => round?.bracket_type === 'placement')
  if (!placementRound?.matches?.length) return null
  return normalizeMatch(placementRound.matches[0], placementRound.round_name || props.thirdPlaceTitle, 0)
})

const showThirdPlaceCard = computed(() =>
  !!thirdPlaceMatch.value || mainRounds.value.length >= 2
)

const displayFinalMatch = computed(() =>
  finalMatch.value || buildPendingMatch(props.finalTitle)
)

const displayThirdPlaceMatch = computed(() =>
  thirdPlaceMatch.value || buildPendingMatch(props.thirdPlaceTitle)
)

const totalRounds = computed(() => mainRounds.value.length)

const layoutStyle = computed(() => {
  const roundsCount = totalRounds.value
  const compactFactor = props.compact ? 1 : 1.14
  const sideWidth =
    roundsCount >= 7 ? 150 :
    roundsCount >= 6 ? 156 :
    roundsCount >= 5 ? 164 :
    roundsCount >= 4 ? 176 :
    roundsCount >= 3 ? 188 : 204
  const centerWidth =
    roundsCount >= 6 ? 220 :
    roundsCount >= 5 ? 230 :
    roundsCount >= 4 ? 244 : 264

  return {
    '--bracket-side-width': `${Math.round(sideWidth * compactFactor)}px`,
    '--bracket-center-width': `${Math.round(centerWidth * compactFactor)}px`,
    '--bracket-gap': props.compact ? '0.7rem' : '1rem',
    '--bracket-padding': props.compact ? '0.75rem' : '1rem',
    '--bracket-slot-padding': props.compact ? '0.5rem 0.6rem' : '0.65rem 0.75rem',
  }
})

function normalizeMatches(matches, roundName) {
  return (matches || [])
    .map((match, matchIdx) => normalizeMatch(match, roundName, matchIdx))
    .filter(Boolean)
}

function normalizeMatch(match, roundName, matchIdx) {
  if (!match) return null
  const explicitLabel = String(match.label || match.match_label || '').trim()
  return {
    id: match.id ?? `${roundName || 'round'}-${matchIdx}`,
    label: explicitLabel || `${roundName || 'Runde'} ${matchIdx + 1}`,
    winner: match.winner || '',
    team1: normalizeSlot(match, 'team1', 'cups_team1'),
    team2: normalizeSlot(match, 'team2', 'cups_team2'),
  }
}

function normalizeSlot(match, teamKey, cupsKey) {
  const teamName = String(match?.[teamKey] || '').trim()
  const winner = String(match?.winner || '').trim()
  const cupsRaw = Number(match?.[cupsKey] ?? 0)
  const cups = Number.isFinite(cupsRaw) ? cupsRaw : 0

  if (!teamName) {
    return {
      sourceLabel: winner ? 'Freilos' : 'Noch offen',
      metaLabel: '',
      isBye: !!winner,
      isWinner: false,
      isLoser: false,
    }
  }

  return {
    sourceLabel: teamName,
    metaLabel: cups > 0 || winner ? `${cups} Becher` : '',
    isBye: false,
    isWinner: !!winner && winner === teamName,
    isLoser: !!winner && winner !== teamName,
  }
}

function buildPendingMatch(label) {
  return {
    id: `placeholder-${label}`,
    label,
    winner: '',
    team1: {
      sourceLabel: 'Noch offen',
      metaLabel: '',
      isBye: false,
      isWinner: false,
      isLoser: false,
    },
    team2: {
      sourceLabel: 'Noch offen',
      metaLabel: '',
      isBye: false,
      isWinner: false,
      isLoser: false,
    },
  }
}

function slotClass(slot) {
  return {
    'bracket-slot--bye': slot.isBye,
    'bracket-slot--winner': slot.isWinner,
    'bracket-slot--loser': slot.isLoser,
  }
}

function isActiveMatch(matchId) {
  if (matchId == null || !props.activeMatchIds) return false
  if (typeof props.activeMatchIds.has === 'function') return props.activeMatchIds.has(matchId)
  if (Array.isArray(props.activeMatchIds)) return props.activeMatchIds.includes(matchId)
  return !!props.activeMatchIds[matchId]
}

// ── Auto-scale: shrink bracket to fit container width ────────────────────
// zoom (unlike transform:scale) affects layout, so the parent collapses
// to the scaled height automatically — no manual height management needed.
const scrollRef  = ref(null)   // .bracket-tree__scroll — observed for available width
const layoutRef  = ref(null)   // .bracket-tree__layout — measured for natural width

const _naturalW = ref(0)
const _naturalH = ref(0)
const _availW   = ref(Infinity)
const _availH   = ref(Infinity)
let   _lastZoom = 1

const autoScale = computed(() => {
  if (!props.constrainToHeight) return 1
  const nw = _naturalW.value
  const aw = _availW.value
  if (!nw || !aw) return 1
  const wScale = aw / nw
  if (!_naturalH.value || _availH.value >= Infinity) {
    return Math.max(0.1, Math.min(1, wScale))
  }
  return Math.max(0.1, Math.min(1, wScale, _availH.value / _naturalH.value))
})

const zoomStyle = computed(() => {
  const s = autoScale.value
  _lastZoom = s
  return { zoom: s }
})

const layoutSignature = computed(() =>
  JSON.stringify(
    (props.rounds || []).map(round => ({
      bracket_type: round?.bracket_type || 'main',
      round_name: round?.round_name || '',
      matches: (round?.matches || []).map(match => ({
        id: match?.id ?? null,
        label: match?.label ?? match?.match_label ?? '',
        team1: match?.team1 ?? '',
        team2: match?.team2 ?? '',
        winner: match?.winner ?? '',
      })),
    }))
  )
)

async function _remeasure() {
  await nextTick()
  const el = layoutRef.value
  if (!el) return
  const w = Math.round(el.scrollWidth  / _lastZoom)
  const h = Math.round(el.scrollHeight / _lastZoom)
  if (w > 0) _naturalW.value = w
  if (h > 0) _naturalH.value = h
}

let _ro = null
onMounted(() => {
  _ro = new ResizeObserver(entries => {
    const rect = entries[0]?.contentRect
    if (!rect) return
    if (rect.width > 0) {
      _availW.value = rect.width
      if (_naturalW.value === 0) _remeasure()
    }
    if (props.constrainToHeight && rect.height > 0) {
      _availH.value = rect.height
    }
  })
  if (scrollRef.value) _ro.observe(scrollRef.value)
  _remeasure()
})
onUnmounted(() => _ro?.disconnect())
watch(layoutSignature, () => _remeasure(), { flush: 'post' })
</script>

<style scoped>
.bracket-tree {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(8, 8, 8, 0.92) 0%, rgba(15, 20, 30, 0.92) 100%);
  overflow: hidden;
}

.bracket-tree__scroll {
  overflow-x: auto;
  overflow-y: hidden;
  padding: var(--bracket-padding);
}

.bracket-tree__layout {
  display: grid;
  grid-template-columns: auto var(--bracket-center-width) auto;
  align-items: center;
  gap: var(--bracket-gap);
  min-width: max-content;
}

.bracket-tree__side {
  display: flex;
  gap: var(--bracket-gap);
  align-items: stretch;
}

.bracket-tree__side--left {
  justify-content: flex-end;
}

.bracket-tree__side--right {
  justify-content: flex-start;
}

.bracket-column {
  width: var(--bracket-side-width);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--bracket-gap);
}

.bracket-column__header {
  display: flex;
  justify-content: center;
}

.bracket-column__header--center {
  justify-content: center;
}

.bracket-column__title {
  display: inline-flex;
  align-items: center;
  padding: 0.36rem 0.68rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-weight: 700;
  font-size: 0.78rem;
  line-height: 1;
  text-align: center;
}

.bracket-column__title--final {
  background: linear-gradient(135deg, rgba(173, 49, 49, 0.8) 0%, rgba(89, 18, 18, 0.85) 100%);
  border: 1px solid rgba(255, 214, 153, 0.2);
}

.bracket-column__matches {
  display: flex;
  flex-direction: column;
  gap: var(--bracket-gap);
  justify-content: center;
}

.bracket-tree__center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--bracket-gap);
  width: var(--bracket-center-width);
}

.bracket-center-card {
  position: relative;
  width: 100%;
  padding: calc(var(--bracket-padding) + 0.1rem);
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.2);
}

.bracket-center-card--final {
  background: linear-gradient(180deg, rgba(77, 19, 19, 0.94) 0%, rgba(36, 10, 10, 0.94) 100%);
  border-color: rgba(255, 214, 153, 0.18);
}

.bracket-center-card--third {
  background: linear-gradient(180deg, rgba(77, 54, 22, 0.62) 0%, rgba(31, 21, 9, 0.92) 100%);
  border-color: rgba(214, 166, 98, 0.18);
}

.bracket-center-card--final::before,
.bracket-center-card--final::after {
  content: '';
  position: absolute;
  top: 50%;
  width: calc(var(--bracket-gap) + 0.1rem);
  height: 2px;
  background: linear-gradient(90deg, rgba(255, 214, 153, 0) 0%, rgba(255, 214, 153, 0.45) 100%);
  transform: translateY(-50%);
}

.bracket-center-card--final::before {
  left: calc(-1 * var(--bracket-gap));
}

.bracket-center-card--final::after {
  right: calc(-1 * var(--bracket-gap));
  transform: translateY(-50%) scaleX(-1);
}

.bracket-match {
  padding: 0.68rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
}

.bracket-match--featured {
  background: rgba(255, 255, 255, 0.05);
}

.bracket-match__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.45rem;
  min-height: 1rem;
}

.bracket-match__label {
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.bracket-live-pulse {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #dc3545;
  flex: 0 0 auto;
  animation: bracket-live-pulse 1.2s ease-in-out infinite;
}

@keyframes bracket-live-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.72);
    opacity: 1;
  }
  50% {
    box-shadow: 0 0 0 6px rgba(220, 53, 69, 0);
    opacity: 0.82;
  }
}

.bracket-match__versus {
  color: rgba(255, 255, 255, 0.36);
  font-size: 0.66rem;
  font-weight: 700;
  text-align: center;
  margin: 0.28rem 0;
}

.bracket-match__winner {
  margin-top: 0.5rem;
  color: #4ade80;
  font-size: 0.74rem;
  font-weight: 700;
  line-height: 1.1;
  min-height: 0.82rem;
}

.bracket-match__winner--hidden {
  visibility: hidden;
}

.bracket-match__winner--gold {
  color: #fbbf24;
}

.bracket-slot {
  padding: var(--bracket-slot-padding);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.92) 0%, rgba(15, 23, 42, 0.92) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  min-height: 3.05rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.bracket-slot--bye {
  opacity: 0.65;
  background: linear-gradient(135deg, rgba(46, 46, 46, 0.88) 0%, rgba(23, 23, 23, 0.88) 100%);
}

.bracket-slot--winner {
  border-color: rgba(74, 222, 128, 0.45);
  background: linear-gradient(135deg, rgba(16, 78, 43, 0.92) 0%, rgba(8, 44, 24, 0.92) 100%);
}

.bracket-slot--loser {
  opacity: 0.68;
}

.bracket-slot__seed {
  display: block;
  color: #fff;
  font-weight: 700;
  line-height: 1.14;
  font-size: 0.8rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bracket-slot__team {
  display: block;
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.74rem;
  margin-top: 0.24rem;
  line-height: 1.18;
  min-height: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bracket-slot__team:empty::before {
  content: '\00a0';
}

.bracket-tree--compact .bracket-match {
  padding: 0.58rem;
}

.bracket-tree--compact .bracket-slot__seed {
  font-size: 0.76rem;
}

.bracket-tree--compact .bracket-slot__team {
  font-size: 0.7rem;
}

/* Kein responsiver Umbruch: Baum bleibt immer horizontal,
   overflow-x: auto auf .bracket-tree__scroll übernimmt das Scrollen. */
</style>
