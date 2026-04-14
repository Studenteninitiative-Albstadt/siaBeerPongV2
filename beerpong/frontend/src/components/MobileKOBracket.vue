<template>
  <div class="mob-ko">
    <div class="mob-ko__scroll">
      <div class="mob-ko__layout" :style="layoutVars">

        <!-- Left side: QF → SF (outer → inner, first-half matches) -->
        <div class="mob-ko__side mob-ko__side--left">
          <section
            v-for="col in leftColumns"
            :key="col.id"
            class="mob-ko__col"
          >
            <header class="mob-ko__col-header">{{ col.name }}</header>
            <div class="mob-ko__col-matches">
              <article v-for="(m, mi) in col.matches" :key="mi" class="mob-ko__match">
                <div class="mob-ko__slot" :class="slotClass(m, 'team1')">
                  {{ m.team1 || '?' }}
                </div>
                <div class="mob-ko__vs">vs</div>
                <div class="mob-ko__slot" :class="slotClass(m, 'team2')">
                  {{ m.team2 || '?' }}
                </div>
                <div v-if="m.winner" class="mob-ko__winner">🏆 {{ m.winner }}</div>
              </article>
            </div>
          </section>
        </div>

        <!-- Center: Final + Platz 3 -->
        <div class="mob-ko__center">
          <section class="mob-ko__center-card">
            <header class="mob-ko__col-header mob-ko__col-header--final">Finale</header>
            <article class="mob-ko__match mob-ko__match--featured">
              <div class="mob-ko__slot" :class="slotClass(finalMatch, 'team1')">
                {{ finalMatch?.team1 || '?' }}
              </div>
              <div class="mob-ko__vs">vs</div>
              <div class="mob-ko__slot" :class="slotClass(finalMatch, 'team2')">
                {{ finalMatch?.team2 || '?' }}
              </div>
              <div v-if="finalMatch?.winner" class="mob-ko__winner mob-ko__winner--gold">
                🏆 {{ finalMatch.winner }}
              </div>
            </article>
          </section>

          <section v-if="thirdMatch" class="mob-ko__center-card mob-ko__center-card--third">
            <header class="mob-ko__col-header">Platz 3</header>
            <article class="mob-ko__match">
              <div class="mob-ko__slot" :class="slotClass(thirdMatch, 'team1')">
                {{ thirdMatch.team1 || '?' }}
              </div>
              <div class="mob-ko__vs">vs</div>
              <div class="mob-ko__slot" :class="slotClass(thirdMatch, 'team2')">
                {{ thirdMatch.team2 || '?' }}
              </div>
              <div v-if="thirdMatch.winner" class="mob-ko__winner">🏆 {{ thirdMatch.winner }}</div>
            </article>
          </section>
        </div>

        <!-- Right side: SF → QF (inner → outer via .reverse(), second-half matches) -->
        <div class="mob-ko__side mob-ko__side--right">
          <section
            v-for="col in rightColumns"
            :key="col.id"
            class="mob-ko__col"
          >
            <header class="mob-ko__col-header">{{ col.name }}</header>
            <div class="mob-ko__col-matches">
              <article v-for="(m, mi) in col.matches" :key="mi" class="mob-ko__match">
                <div class="mob-ko__slot" :class="slotClass(m, 'team1')">
                  {{ m.team1 || '?' }}
                </div>
                <div class="mob-ko__vs">vs</div>
                <div class="mob-ko__slot" :class="slotClass(m, 'team2')">
                  {{ m.team2 || '?' }}
                </div>
                <div v-if="m.winner" class="mob-ko__winner">🏆 {{ m.winner }}</div>
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
  rounds: { type: Array, default: () => [] },
})

// Split into main rounds (no placement) and 3rd-place round
const mainRounds   = computed(() => props.rounds.filter(r => r.bracket_type !== 'placement'))
const preFinal     = computed(() => mainRounds.value.slice(0, -1))
const finalRound   = computed(() => mainRounds.value[mainRounds.value.length - 1] ?? null)
const finalMatch   = computed(() => finalRound.value?.matches?.[0] ?? null)
const thirdMatch   = computed(() => {
  const p = props.rounds.find(r => r.bracket_type === 'placement')
  return p?.matches?.[0] ?? null
})

// Left side: preFinal rounds, first half of matches each, outer → inner
const leftColumns = computed(() =>
  preFinal.value
    .map(r => ({
      id:      'left-' + r.round_name,
      name:    r.round_name,
      matches: r.matches.slice(0, Math.ceil(r.matches.length / 2)),
    }))
    .filter(c => c.matches.length > 0)
)

// Right side: preFinal rounds, second half of matches each, reversed (inner → outer)
const rightColumns = computed(() =>
  preFinal.value
    .map(r => ({
      id:      'right-' + r.round_name,
      name:    r.round_name,
      matches: r.matches.slice(Math.ceil(r.matches.length / 2)),
    }))
    .filter(c => c.matches.length > 0)
    .reverse()
)

// CSS variables: column width shrinks as more rounds are present
const layoutVars = computed(() => {
  const n = preFinal.value.length   // 0 for 4-team (only final), 1 for 4-team SF, 2 for 8-team, etc.
  const colW    = n >= 3 ? 80 : n >= 2 ? 88 : 96
  const centerW = 110
  return {
    '--mob-col-w':      colW    + 'px',
    '--mob-center-w':   centerW + 'px',
  }
})

function slotClass(match, team) {
  if (!match?.winner) return ''
  return match.winner === match[team] ? 'mob-ko__slot--winner' : 'mob-ko__slot--loser'
}
</script>

<style scoped>
/* ── Outer scroll container — always scrolls, never collapses ───────────── */
.mob-ko {
  overflow-x: auto;
  overflow-y: visible;
  -webkit-overflow-scrolling: touch;
  width: 100%;
}

.mob-ko__scroll {
  display: inline-block; /* sizes to content, not parent width — scroll container can detect overflow */
  min-width: 100%;       /* at least full viewport width when bracket is narrow */
  padding: 0.25rem 0.2rem 0.5rem;
}

/* ── Three-column flex row — inline-flex sizes to content, never wraps ──── */
.mob-ko__layout {
  display: inline-flex;   /* sizes to content; ignores parent width */
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 0.25rem;
  align-items: flex-start;
}

/* ── Side panels ─────────────────────────────────────────────────────────  */
.mob-ko__side {
  flex: 0 0 auto;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 0.25rem;
  align-items: flex-start;
}

/* ── Single round column ─────────────────────────────────────────────────  */
.mob-ko__col {
  flex: 0 0 var(--mob-col-w);
  width: var(--mob-col-w);
  min-width: var(--mob-col-w);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.mob-ko__col-header {
  background: linear-gradient(135deg, #1f2630, #15181c);
  border: 1px solid rgba(108,117,125,0.6);
  border-radius: 6px;
  padding: 0.16rem 0.25rem;
  font-size: 0.54rem;
  font-weight: 600;
  color: #f8f9fa;
  text-align: center;
  white-space: nowrap;
}

.mob-ko__col-matches {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  gap: 0.2rem;
}

/* ── Match card ──────────────────────────────────────────────────────────  */
.mob-ko__match {
  background: radial-gradient(circle at top left, rgba(255,255,255,0.03), rgba(0,0,0,0.88));
  border: 1px solid rgba(73,80,87,0.85);
  border-radius: 6px;
  padding: 0.2rem 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.07rem;
}

.mob-ko__match--featured {
  border-color: rgba(255, 200, 50, 0.45);
  background: radial-gradient(circle at top left, rgba(255,200,50,0.05), rgba(0,0,0,0.92));
}

/* ── Team slot ───────────────────────────────────────────────────────────  */
.mob-ko__slot {
  font-size: 0.56rem;
  color: #c8d2dc;
  padding: 0.1rem 0.2rem;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s, background 0.2s;
  line-height: 1.3;
}

.mob-ko__slot--winner {
  color: #4ade80;
  font-weight: 700;
  background: rgba(74,222,128,0.1);
}

.mob-ko__slot--loser {
  color: rgba(200,210,220,0.38);
  text-decoration: line-through;
}

.mob-ko__vs {
  font-size: 0.44rem;
  color: rgba(255,255,255,0.3);
  text-align: center;
  line-height: 1;
}

.mob-ko__winner {
  font-size: 0.5rem;
  color: #4ade80;
  text-align: center;
  padding-top: 0.08rem;
  border-top: 1px solid rgba(74,222,128,0.2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mob-ko__winner--gold {
  color: #fbbf24;
  border-top-color: rgba(251,191,36,0.25);
}

/* ── Center column ───────────────────────────────────────────────────────  */
.mob-ko__center {
  flex: 0 0 var(--mob-center-w);
  width: var(--mob-center-w);
  min-width: var(--mob-center-w);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  align-self: center;
}

.mob-ko__center-card {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.mob-ko__col-header--final {
  background: linear-gradient(135deg, #2a1f10, #1c1208);
  border-color: rgba(255,200,50,0.4);
  color: #fbbf24;
}

.mob-ko__center-card--third .mob-ko__col-header {
  font-size: 0.5rem;
  background: linear-gradient(135deg, #151a20, #0e1115);
}
</style>
