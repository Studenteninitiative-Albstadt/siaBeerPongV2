<template>
  <div class="bracket-tree" :class="{ 'bracket-tree--compact': compact }" :style="layoutStyle">
    <div class="bracket-tree__scroll">
      <div class="bracket-tree__layout">
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
                <div class="bracket-match__label">{{ match.label }}</div>
                <div class="bracket-slot" :class="{ 'bracket-slot--bye': match.team1.isBye }">
                  <div class="bracket-slot__seed">{{ match.team1.sourceLabel }}</div>
                  <div
                    v-if="match.team1.teamName && match.team1.teamName !== match.team1.sourceLabel"
                    class="bracket-slot__team"
                  >
                    {{ match.team1.teamName }}
                  </div>
                </div>
                <div class="bracket-match__versus">vs</div>
                <div class="bracket-slot" :class="{ 'bracket-slot--bye': match.team2.isBye }">
                  <div class="bracket-slot__seed">{{ match.team2.sourceLabel }}</div>
                  <div
                    v-if="match.team2.teamName && match.team2.teamName !== match.team2.sourceLabel"
                    class="bracket-slot__team"
                  >
                    {{ match.team2.teamName }}
                  </div>
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
            <article v-if="finalMatch" class="bracket-match bracket-match--featured">
              <div class="bracket-match__label">{{ finalMatch.label }}</div>
              <div class="bracket-slot">
                <div class="bracket-slot__seed">{{ finalMatch.team1.sourceLabel }}</div>
                <div
                  v-if="finalMatch.team1.teamName && finalMatch.team1.teamName !== finalMatch.team1.sourceLabel"
                  class="bracket-slot__team"
                >
                  {{ finalMatch.team1.teamName }}
                </div>
              </div>
              <div class="bracket-match__versus">vs</div>
              <div class="bracket-slot">
                <div class="bracket-slot__seed">{{ finalMatch.team2.sourceLabel }}</div>
                <div
                  v-if="finalMatch.team2.teamName && finalMatch.team2.teamName !== finalMatch.team2.sourceLabel"
                  class="bracket-slot__team"
                >
                  {{ finalMatch.team2.teamName }}
                </div>
              </div>
            </article>
          </section>

          <section
            v-if="thirdPlaceMatch"
            class="bracket-center-card bracket-center-card--third"
          >
            <header class="bracket-column__header bracket-column__header--center">
              <span class="bracket-column__title">{{ thirdPlaceTitle }}</span>
            </header>
            <article class="bracket-match">
              <div class="bracket-match__label">{{ thirdPlaceMatch.label }}</div>
              <div class="bracket-slot">
                <div class="bracket-slot__seed">{{ thirdPlaceMatch.team1.sourceLabel }}</div>
              </div>
              <div class="bracket-match__versus">vs</div>
              <div class="bracket-slot">
                <div class="bracket-slot__seed">{{ thirdPlaceMatch.team2.sourceLabel }}</div>
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
                <div class="bracket-match__label">{{ match.label }}</div>
                <div class="bracket-slot" :class="{ 'bracket-slot--bye': match.team1.isBye }">
                  <div class="bracket-slot__seed">{{ match.team1.sourceLabel }}</div>
                  <div
                    v-if="match.team1.teamName && match.team1.teamName !== match.team1.sourceLabel"
                    class="bracket-slot__team"
                  >
                    {{ match.team1.teamName }}
                  </div>
                </div>
                <div class="bracket-match__versus">vs</div>
                <div class="bracket-slot" :class="{ 'bracket-slot--bye': match.team2.isBye }">
                  <div class="bracket-slot__seed">{{ match.team2.sourceLabel }}</div>
                  <div
                    v-if="match.team2.teamName && match.team2.teamName !== match.team2.sourceLabel"
                    class="bracket-slot__team"
                  >
                    {{ match.team2.teamName }}
                  </div>
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
import { computed } from 'vue'

const props = defineProps({
  slots: { type: Array, default: () => [] },
  bracketSize: { type: Number, default: null },
  compact: { type: Boolean, default: false },
  showThirdPlace: { type: Boolean, default: true },
  finalTitle: { type: String, default: 'Finale' },
  thirdPlaceTitle: { type: String, default: 'Spiel um Platz 3' },
})

const resolvedBracketSize = computed(() => {
  const requestedSize = Math.max(
    2,
    Number(props.bracketSize) || 0,
    props.slots.length || 0
  )
  return nextPowerOfTwo(requestedSize)
})

const normalizedSlots = computed(() => {
  const base = (props.slots || []).map((slot, idx) => ({
    id: slot.id ?? `slot-${idx}`,
    sourceLabel: slot.sourceLabel || slot.label || slot.teamName || `Slot ${idx + 1}`,
    teamName: slot.teamName || slot.team || '',
    isBye: !!slot.isBye,
  }))

  while (base.length < resolvedBracketSize.value) {
    base.push({
      id: `bye-${base.length}`,
      sourceLabel: 'Freilos',
      teamName: '',
      isBye: true,
    })
  }

  return base.slice(0, resolvedBracketSize.value)
})

const rounds = computed(() => {
  const totalRounds = Math.max(1, Math.ceil(Math.log2(Math.max(2, resolvedBracketSize.value))))
  const result = []
  let current = normalizedSlots.value

  for (let roundIdx = 0; roundIdx < totalRounds; roundIdx++) {
    const matches = []
    const next = []
    const roundName = roundNameFor(totalRounds, roundIdx)
    const shortToken = roundTokenFor(totalRounds, roundIdx)

    for (let i = 0; i < current.length; i += 2) {
      const matchIndex = Math.floor(i / 2)
      const team1 = current[i]
      const team2 = current[i + 1]
      if (!team1 || !team2) continue

      matches.push({
        id: `r${roundIdx}-m${matchIndex}`,
        label: `${roundName} ${matchIndex + 1}`,
        team1,
        team2,
      })

      if (roundIdx < totalRounds - 1) {
        next.push({
          id: `winner-${roundIdx}-${matchIndex}`,
          sourceLabel: `Sieger ${shortToken} ${matchIndex + 1}`,
          teamName: '',
          isBye: false,
        })
      }
    }

    result.push({
      id: `round-${roundIdx}`,
      name: roundName,
      matches,
    })
    current = next
  }

  return result
})

const sideRounds = computed(() => rounds.value.slice(0, -1))

const leftColumns = computed(() =>
  sideRounds.value
    .map(round => ({
      id: `left-${round.id}`,
      name: round.name,
      matches: round.matches.slice(0, Math.ceil(round.matches.length / 2)),
    }))
    .filter(column => column.matches.length)
)

const rightColumns = computed(() =>
  sideRounds.value
    .map(round => ({
      id: `right-${round.id}`,
      name: round.name,
      matches: round.matches.slice(Math.ceil(round.matches.length / 2)),
    }))
    .filter(column => column.matches.length)
    .reverse()
)

const finalMatch = computed(() => {
  const lastRound = rounds.value[rounds.value.length - 1]
  return lastRound?.matches?.[0] ?? null
})

const thirdPlaceMatch = computed(() => {
  if (!props.showThirdPlace || rounds.value.length < 2) return null
  return {
    id: 'third-place-match',
    label: props.thirdPlaceTitle,
    team1: {
      id: 'loser-hf-1',
      sourceLabel: 'Verlierer HF 1',
      teamName: '',
      isBye: false,
    },
    team2: {
      id: 'loser-hf-2',
      sourceLabel: 'Verlierer HF 2',
      teamName: '',
      isBye: false,
    },
  }
})

const totalRounds = computed(() => rounds.value.length)

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

function nextPowerOfTwo(value) {
  let size = 2
  while (size < Math.max(2, value)) size *= 2
  return size
}

function roundNameFor(totalRoundsCount, roundIdx) {
  const names = {
    1: ['Finale'],
    2: ['Halbfinale', 'Finale'],
    3: ['Viertelfinale', 'Halbfinale', 'Finale'],
    4: ['Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale'],
    5: ['Runde der 32', 'Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale'],
    6: ['Runde der 64', 'Runde der 32', 'Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale'],
    7: ['Runde der 128', 'Runde der 64', 'Runde der 32', 'Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale'],
    8: ['Runde der 256', 'Runde der 128', 'Runde der 64', 'Runde der 32', 'Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale'],
  }
  return names[totalRoundsCount]?.[roundIdx] || `Runde ${roundIdx + 1}`
}

function roundTokenFor(totalRoundsCount, roundIdx) {
  const tokens = {
    1: ['F'],
    2: ['HF', 'F'],
    3: ['VF', 'HF', 'F'],
    4: ['AF', 'VF', 'HF', 'F'],
    5: ['R32', 'AF', 'VF', 'HF', 'F'],
    6: ['R64', 'R32', 'AF', 'VF', 'HF', 'F'],
    7: ['R128', 'R64', 'R32', 'AF', 'VF', 'HF', 'F'],
    8: ['R256', 'R128', 'R64', 'R32', 'AF', 'VF', 'HF', 'F'],
  }
  return tokens[totalRoundsCount]?.[roundIdx] || `R${roundIdx + 1}`
}
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

.bracket-match__label {
  margin-bottom: 0.45rem;
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.bracket-match__versus {
  color: rgba(255, 255, 255, 0.36);
  font-size: 0.66rem;
  font-weight: 700;
  text-align: center;
  margin: 0.28rem 0;
}

.bracket-slot {
  padding: var(--bracket-slot-padding);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.92) 0%, rgba(15, 23, 42, 0.92) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.bracket-slot--bye {
  opacity: 0.65;
  background: linear-gradient(135deg, rgba(46, 46, 46, 0.88) 0%, rgba(23, 23, 23, 0.88) 100%);
}

.bracket-slot__seed {
  color: #fff;
  font-weight: 700;
  line-height: 1.14;
  font-size: 0.8rem;
}

.bracket-slot__team {
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.74rem;
  margin-top: 0.24rem;
  line-height: 1.18;
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

@media (max-width: 1200px) {
  .bracket-tree__layout {
    grid-template-columns: 1fr;
    min-width: 0;
  }

  .bracket-tree__side {
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 0.2rem;
  }

  .bracket-tree__center {
    width: min(100%, var(--bracket-center-width));
    justify-self: center;
  }

  .bracket-center-card--final::before,
  .bracket-center-card--final::after {
    display: none;
  }
}
</style>
