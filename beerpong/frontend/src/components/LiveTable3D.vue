<template>
  <div class="beer-table" :class="{ 'beer-table--compact': compact, 'beer-table--beam': beam }">
    <!-- Team 2 (top) -->
    <div class="beer-table__team beer-table__team--top">
      <div class="beer-table__name">{{ match?.team2 || '?' }}</div>
      <div v-if="team2Players" class="beer-table__players">{{ team2Players }}</div>
    </div>

    <div class="beer-table__stage">
      <div class="beer-table__surface">

        <!-- Team 2 Becher – Ball kommt von UNTEN (Team 1 schießt nach oben) -->
        <div class="beer-table__cups beer-table__cups--top">
          <div v-for="(row, rIdx) in team2Rows" :key="`t2-row-${rIdx}`" class="beer-table__row">
            <div
              v-for="cup in row"
              :key="`t2-${cup.idx}`"
              :ref="el => { if (el) cupRefs2[cup.idx] = el; else delete cupRefs2[cup.idx] }"
              class="beer-cup"
              :class="{
                'beer-cup--hit':     !cup.val && !animatingTeam2.has(cup.idx),
                'beer-cup--scoring':  animatingTeam2.has(cup.idx)
              }"
            >
              <span class="beer-cup__body"></span>
              <span class="beer-cup__ridge"></span>
              <span class="beer-cup__highlight"></span>
              <span class="beer-cup__rim"></span>
              <span class="beer-cup__opening"></span>
              <span class="beer-cup__shadow"></span>
            </div>
          </div>
        </div>

        <div class="beer-table__net-wrap">
          <span class="beer-table__net"></span>
        </div>

        <!-- Team 1 Becher – Ball kommt von OBEN (Team 2 schießt nach unten) -->
        <div class="beer-table__cups beer-table__cups--bottom">
          <div v-for="(row, rIdx) in team1Rows" :key="`t1-row-${rIdx}`" class="beer-table__row">
            <div
              v-for="cup in row"
              :key="`t1-${cup.idx}`"
              :ref="el => { if (el) cupRefs1[cup.idx] = el; else delete cupRefs1[cup.idx] }"
              class="beer-cup"
              :class="{
                'beer-cup--hit':     !cup.val && !animatingTeam1.has(cup.idx),
                'beer-cup--scoring':  animatingTeam1.has(cup.idx)
              }"
            >
              <span class="beer-cup__body"></span>
              <span class="beer-cup__ridge"></span>
              <span class="beer-cup__highlight"></span>
              <span class="beer-cup__rim"></span>
              <span class="beer-cup__opening"></span>
              <span class="beer-cup__shadow"></span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Team 1 (bottom) -->
    <div class="beer-table__team beer-table__team--bottom">
      <div class="beer-table__name">{{ match?.team1 || '?' }}</div>
      <div v-if="team1Players" class="beer-table__players">{{ team1Players }}</div>
      <div v-if="showScore" class="beer-table__score">
        {{ match?.cups_team1 ?? 0 }} : {{ match?.cups_team2 ?? 0 }} Becher
      </div>
    </div>

    <div v-if="tableLabel" class="beer-table__label">{{ tableLabel }}</div>
  </div>

  <!-- ── Ball & splash — teleported to body, completely outside the 3D hierarchy ── -->
  <!-- position: fixed relative to viewport, so z-ordering is trivial                -->
  <Teleport to="body">
    <div
      v-for="anim in animations"
      :key="anim.id"
      class="ball-overlay"
      :style="{
        left:       anim.cx + 'px',
        top:        anim.cy + 'px',
        '--bs':     anim.bs     + 'px',
        '--travel': anim.travel + 'px',
      }"
    >
      <span class="ball-anim" :class="`ball-anim--${anim.direction}`"></span>
      <span class="splash-burst"></span>
      <span class="splash-ring"></span>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  match:        { type: Object,  required: true },
  cupsPerGame:  { type: Number,  default: 6 },
  team1Players: { type: String,  default: '' },
  team2Players: { type: String,  default: '' },
  tableLabel:   { type: String,  default: '' },
  compact:      { type: Boolean, default: false },
  beam:         { type: Boolean, default: false },
  showScore:    { type: Boolean, default: false },
})

// ── Cup DOM refs — used to get viewport coordinates for ball animations ──────
// Plain objects (not reactive): we only read them inside triggerHit, never bind reactively.
const cupRefs1 = {}
const cupRefs2 = {}

// ── Animation state ────────────────────────────────────────────────────────────
// Each entry: { id, team, idx, cx, cy, bs (ball size px), travel (px), direction }
const animations = ref([])
let nextAnimId = 0
const ANIM_MS = 1400

// Derived Sets used for cup CSS classes
const animatingTeam1 = computed(() => new Set(animations.value.filter(a => a.team === 1).map(a => a.idx)))
const animatingTeam2 = computed(() => new Set(animations.value.filter(a => a.team === 2).map(a => a.idx)))

// Local copies of previous cup states
const prevCups1 = ref(null)
const prevCups2 = ref(null)

async function triggerHit(team, idx) {
  // Wait for Vue to render the cup before reading its screen position
  await nextTick()
  const refs = team === 1 ? cupRefs1 : cupRefs2
  const el   = refs[idx]
  let cx = 0, cy = 0, bs = 11, travel = 130
  if (el) {
    const r = el.getBoundingClientRect()
    cx     = r.left + r.width  / 2
    cy     = r.top  + r.height / 2
    bs     = Math.max(8, Math.round(r.width * 0.36))   // ~36 % of cup width
    travel = Math.max(80, Math.round(r.width * 4.8))   // ~4.8× cup width
  }
  const id        = ++nextAnimId
  const direction = team === 1 ? 'from-above' : 'from-below'
  animations.value = [...animations.value, { id, team, idx, cx, cy, bs, travel, direction }]
  setTimeout(() => {
    animations.value = animations.value.filter(a => a.id !== id)
  }, ANIM_MS)
}

watch(() => props.match?.cups_state_team1, (next) => {
  if (!Array.isArray(next)) return
  if (next.length === 0) {
    // Backend-Initialzustand (noch keine Treffer): als "alle lebendig" merken
    prevCups1.value = []
    return
  }
  if (prevCups1.value === null) {
    // Komponente mitten im Spiel eingehängt: gespeicherten Zustand setzen, KEINE Animation
    prevCups1.value = [...next]
    return
  }
  const prev = prevCups1.value
  // prev.length === 0 bedeutet cups_state war [] → alle Becher waren lebendig
  next.forEach((val, idx) => {
    const prevVal = prev.length === 0 ? true : (idx < prev.length ? prev[idx] : true)
    if (prevVal === true && val === false) triggerHit(1, idx)
  })
  prevCups1.value = [...next]
}, { deep: true, immediate: true })

watch(() => props.match?.cups_state_team2, (next) => {
  if (!Array.isArray(next)) return
  if (next.length === 0) {
    prevCups2.value = []
    return
  }
  if (prevCups2.value === null) {
    prevCups2.value = [...next]
    return
  }
  const prev = prevCups2.value
  next.forEach((val, idx) => {
    const prevVal = prev.length === 0 ? true : (idx < prev.length ? prev[idx] : true)
    if (prevVal === true && val === false) triggerHit(2, idx)
  })
  prevCups2.value = [...next]
}, { deep: true, immediate: true })

// ── Pyramid layout ────────────────────────────────────────────────────────────
const isTenCupLayout = computed(() => Number(props.cupsPerGame) === 10)
const team1Rows = computed(() => buildPyramid(props.match?.cups_state_team1, isTenCupLayout.value))
const team2Rows = computed(() => buildPyramid(props.match?.cups_state_team2, isTenCupLayout.value))

function buildPyramid(arr, is10) {
  const size = is10 ? 10 : 6
  const a = Array.isArray(arr) && arr.length > 0 ? arr : Array(size).fill(true)
  if (is10) return [
    [0,1,2,3].map(i => ({ idx: i, val: a[i] })),
    [4,5,6  ].map(i => ({ idx: i, val: a[i] })),
    [7,8    ].map(i => ({ idx: i, val: a[i] })),
    [       [{ idx: 9, val: a[9] }]][0],
  ]
  return [
    [0,1,2].map(i => ({ idx: i, val: a[i] })),
    [3,4  ].map(i => ({ idx: i, val: a[i] })),
    [{ idx: 5, val: a[5] }],
  ]
}
</script>

<style scoped>
/* ── Variables ───────────────────────────────────────────────────────────── */
.beer-table {
  /* Master Variable */
  --tw:    220px;

  /* Proportional derivations */
  --ratio: 2.2; /* Table is 2.2x as long as wide */
  --th:    calc(var(--tw) * var(--ratio));
  --cs:    calc(var(--tw) * 0.135); /* Cup size is ~13.5% of width */
  --cg:    calc(var(--tw) * 0.04);  /* Gap is 4% of width */
  --tp:    calc(var(--th) * 0.04);  /* Padding top/bottom is 4% of height */

  --tb:    4px;
  --tilt:  25deg;
  --nf:    1.45rem;
  --gaptop:  0.9rem;
  --gapbot:  1rem;
  --labelf:  0.95rem;

  display: flex;
  flex-direction: column;
  align-items: center;
}

.beer-table--compact {
  --tw:    140px;
  --ratio: 1.8;
  --nf:    1.1rem;
  --gaptop:  0.65rem;
  --gapbot:  0.75rem;
  --labelf:  0.85rem;
}

.beer-table--beam {
  /* On beam, we want it to scale with viewport width, but keep proportions */
  --tw:    clamp(140px, 12vw, 240px);
  --ratio: 2.4; /* Longer for beam */
  --nf:    clamp(1rem, 1.2vw, 1.35rem);
  --labelf: clamp(0.75rem, 0.9vw, 0.95rem);
}

/* ── Team labels ─────────────────────────────────────────────────────────── */
.beer-table__team       { text-align: center; z-index: 2; width: 100%; }
.beer-table__team--top  { margin-bottom: var(--gaptop); }
.beer-table__team--bottom { margin-top: var(--gapbot); }

.beer-table__name {
  color: #fff;
  font-size: var(--nf);
  font-weight: 800;
  letter-spacing: 0.01em;
  text-shadow: 0 2px 10px rgba(0,0,0,0.8);
  line-height: 1.15;
}
.beer-table__players {
  color: rgba(255,255,255,0.48);
  font-size: 0.78rem;
  margin-top: 0.18rem;
}
.beer-table__score {
  color: rgba(255,255,255,0.6);
  font-size: 0.8rem;
  margin-top: 0.3rem;
}

/* ── Stage & surface ─────────────────────────────────────────────────────── */
.beer-table__stage {
  perspective: 1600px;
  display: flex;
  justify-content: center;
  width: 100%;
}

.beer-table__surface {
  width: var(--tw);
  height: var(--th);
  padding: var(--tp) 0;

  background:
    radial-gradient(ellipse at 50% 6%, rgba(255,255,255,0.055) 0%, transparent 35%),
    linear-gradient(180deg,
      #173829 0%,
      #0e2820 35%,
      #081a15 68%,
      #040d0b 100%
    );

  /* Subtle dark outline — no wood/brown */
  border: var(--tb) solid rgba(255,255,255,0.09);
  border-radius: 8px;

  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: visible;

  transform: rotateX(var(--tilt));
  transform-style: preserve-3d;

  box-shadow:
    0 30px 40px rgba(0,0,0,0.65),
    0 0 0 1px rgba(255,255,255,0.03),
    inset 0 1px 0 rgba(255,255,255,0.07),
    inset 0 -10px 22px rgba(0,0,0,0.35);
}

/* Depth face below the table */
.beer-table__surface::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 0; right: 0;
  height: 10px;
  background: linear-gradient(to bottom, rgba(0,0,0,0.55), transparent);
  border-radius: 0 0 6px 6px;
  transform: translateZ(-1px);
}

/* ── Centre net ──────────────────────────────────────────────────────────── */
.beer-table__net-wrap {
  position: absolute;
  top: 50%;
  left: 0; right: 0;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  pointer-events: none;
}
.beer-table__net {
  display: block;
  width: 110%;
  margin-left: -5%;
  height: 2px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255,255,255,0.12) 6%,
    rgba(255,255,255,0.78) 18%,
    rgba(255,255,255,0.78) 82%,
    rgba(255,255,255,0.12) 94%,
    transparent 100%
  );
  box-shadow: 0 0 6px rgba(255,255,255,0.2);
}

/* ── Cup rows ────────────────────────────────────────────────────────────── */
.beer-table__cups {
  height: 44%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: var(--cg);
  transform-style: preserve-3d;
}
.beer-table__cups--top { justify-content: flex-start; }
.beer-table__cups--bottom { flex-direction: column-reverse; }

.beer-table__row {
  display: flex;
  gap: var(--cg);
  transform-style: preserve-3d;
}

/* ── Cup base element ────────────────────────────────────────────────────── */
.beer-cup {
  width:    var(--cs);
  height:   calc(var(--cs) * 1.55);
  position: relative;
  overflow: visible;
  /* Counter-rotate cups to face the camera — no preserve-3d so overflow isn't clipped */
  transform: translateZ(10px) rotateX(calc(var(--tilt) * -1));
  transition:
    transform 0.3s ease,
    opacity   0.3s ease,
    filter    0.3s ease;
}

/* Conical cup body — tapers from wide rim to narrow base */
.beer-cup__body {
  position: absolute;
  inset: 0;
  clip-path: polygon(9% 15%, 91% 15%, 83% 92%, 17% 92%);
  background: linear-gradient(
    105deg,
    #6d0c0c  0%,
    #b82020 16%,
    #e03c3c 42%,
    #d42828 70%,
    #7a0e0e 100%
  );
  box-shadow:
    inset -4px 0 8px rgba(0,0,0,0.25),
    inset  3px 0 6px rgba(255,255,255,0.07);
}

/* Subtle horizontal ridge ~1/3 down */
.beer-cup__ridge {
  position: absolute;
  left: 10%; right: 10%;
  top: 38%;
  height: 8%;
  clip-path: polygon(5% 0%, 95% 0%, 93% 100%, 7% 100%);
  background: rgba(0,0,0,0.14);
  border-radius: 1px;
}

/* Specular highlight stripe */
.beer-cup__highlight {
  position: absolute;
  left: 23%;
  top: 20%;
  width: 9%;
  height: 50%;
  border-radius: 999px;
  background: linear-gradient(to bottom,
    rgba(255,255,255,0.55) 0%,
    rgba(255,255,255,0.04) 100%
  );
  pointer-events: none;
}

/* Wider rim at the top */
.beer-cup__rim {
  position: absolute;
  left: 4%; right: 4%;
  top: 5%;
  height: 18%;
  border-radius: 50%;
  background: linear-gradient(to bottom,
    #ff9090 0%,
    #d83636 55%,
    #8e1515 100%
  );
  box-shadow:
    inset 0 2px 3px rgba(255,255,255,0.28),
    0 1px 5px rgba(0,0,0,0.3);
}

/* Dark opening with beer-amber interior */
.beer-cup__opening {
  position: absolute;
  left: 18%; right: 18%;
  top: 8%;
  height: 10%;
  border-radius: 50%;
  background: radial-gradient(
    ellipse at 46% 36%,
    rgba(180,110,12,0.88),
    rgba(55,18,0,0.98)
  );
  box-shadow: inset 0 -1px 3px rgba(255,190,40,0.1);
}

/* Drop shadow on the table surface */
.beer-cup__shadow {
  position: absolute;
  left: 14%; right: 14%;
  bottom: 2%;
  height: 14%;
  border-radius: 50%;
  background: rgba(0,0,0,0.36);
  filter: blur(4px);
  transform: scaleY(0.4);
}

/* ── Cup states ──────────────────────────────────────────────────────────── */
.beer-cup--hit {
  opacity: 0.09;
  filter: saturate(0) brightness(2);
  transform: translateZ(4px) rotateX(calc(var(--tilt) * -1)) scale(0.6);
}

/* Keep fully visible while scoring animation runs */
.beer-cup--scoring {
  opacity: 1 !important;
  filter: none !important;
  transform: translateZ(10px) rotateX(calc(var(--tilt) * -1)) !important;
}

/* ── Table label badge ───────────────────────────────────────────────────── */
.beer-table__label {
  margin-top: 0.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #f5c84c 0%, #e09820 100%);
  color: #1c1202;
  font-size: var(--labelf);
  font-weight: 700;
  letter-spacing: 0.02em;
  box-shadow: 0 6px 16px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,200,50,0.18);
}
</style>

<!-- ── Ball & splash overlay — non-scoped so selectors are truly global ─────── -->
<style>
/* Anchored at cup center (position:fixed, left/top = cup center in viewport).
   CSS vars --bs (ball size px) and --travel (flight px) set via inline style. */
.ball-overlay {
  position: fixed;
  width: 0;
  height: 0;
  pointer-events: none;
  z-index: 9999;
}

/* ── Ping-pong ball ─────────────────────────────────────────────────────── */
.ball-overlay .ball-anim {
  position: absolute;
  width:  var(--bs);
  height: var(--bs);
  border-radius: 50%;
  left: calc(var(--bs) * -0.5);
  top:  calc(var(--bs) * -0.5);
  pointer-events: none;
  background: radial-gradient(circle at 30% 28%, #ffffff 0%, #e6e6e6 50%, #bbbbbb 100%);
  box-shadow: 0 2px 6px rgba(0,0,0,0.6), inset 0 -1px 2px rgba(0,0,0,0.15);
}

.ball-anim--from-below {
  animation: ball-from-below 0.95s cubic-bezier(0.22, 0.58, 0.46, 0.96) forwards;
}
@keyframes ball-from-below {
  0%   { transform: translate(calc(var(--bs) * -0.4),  var(--travel))              scale(1.12); opacity: 1;   }
  20%  { transform: translate(calc(var(--bs) * -0.25), calc(var(--travel) * 0.62)) scale(1.07); opacity: 1;   }
  48%  { transform: translate(calc(var(--bs) * -0.1),  calc(var(--travel) * 0.24)) scale(1.02); opacity: 1;   }
  70%  { transform: translate(calc(var(--bs) * -0.03), calc(var(--travel) * 0.06)) scale(1);    opacity: 1;   }
  84%  { transform: translate(0,                        calc(var(--bs) * 0.06))    scale(0.8);  opacity: 0.9; }
  94%  { transform: translate(0,                        calc(var(--bs) * -0.04))   scale(0.45); opacity: 0.5; }
  100% { transform: translate(0,                        0)                         scale(0.06); opacity: 0;   }
}

.ball-anim--from-above {
  animation: ball-from-above 0.95s cubic-bezier(0.22, 0.58, 0.46, 0.96) forwards;
}
@keyframes ball-from-above {
  0%   { transform: translate(calc(var(--bs) * 0.4),   calc(var(--travel) * -1))   scale(1.12); opacity: 1;   }
  20%  { transform: translate(calc(var(--bs) * 0.25),  calc(var(--travel) * -0.62))scale(1.07); opacity: 1;   }
  48%  { transform: translate(calc(var(--bs) * 0.1),   calc(var(--travel) * -0.24))scale(1.02); opacity: 1;   }
  70%  { transform: translate(calc(var(--bs) * 0.03),  calc(var(--travel) * -0.06))scale(1);    opacity: 1;   }
  84%  { transform: translate(0,                        calc(var(--bs) * -0.06))   scale(0.8);  opacity: 0.9; }
  94%  { transform: translate(0,                        calc(var(--bs) *  0.04))   scale(0.45); opacity: 0.5; }
  100% { transform: translate(0,                        0)                         scale(0.06); opacity: 0;   }
}

/* ── Splash burst — small water crown, 11 tight droplets via box-shadow ──── */
/* Core 0.6×bs; center at cup opening (~1.7×bs above cup center).
   top = -(1.7×bs) - (0.5 × 0.6×bs) = -2.0×bs                             */
.ball-overlay .splash-burst {
  position: absolute;
  left: calc(var(--bs) * -0.3);
  top:  calc(var(--bs) * -2.0);
  width:  calc(var(--bs) * 0.6);
  height: calc(var(--bs) * 0.6);
  border-radius: 50%;
  background: rgba(210, 245, 255, 0.95);
  opacity: 0;
  pointer-events: none;
  animation: splash-burst-anim 0.50s ease-out 0.80s forwards;
}

@keyframes splash-burst-anim {
  0% {
    opacity: 1;
    transform: scale(1.1);
    box-shadow:
       0px  -9px  0 2px rgba(200,242,255,1.00),   /* straight up */
      -6px  -8px  0 2px rgba(200,242,255,0.92),   /* upper-left */
       6px  -8px  0 2px rgba(200,242,255,0.92),   /* upper-right */
     -10px  -3px  0 1px rgba(185,232,255,0.85),   /* left */
      10px  -3px  0 1px rgba(185,232,255,0.85),   /* right */
      -3px -11px  0 1px rgba(200,242,255,0.82),   /* steep-left */
       3px -11px  0 1px rgba(200,242,255,0.82),   /* steep-right */
      -8px  -6px  0 1px rgba(200,242,255,0.68),   /* mid-left */
       8px  -6px  0 1px rgba(200,242,255,0.68),   /* mid-right */
      -2px   4px  0 1px rgba(185,232,255,0.45),   /* slight-down-left */
       2px   4px  0 1px rgba(185,232,255,0.45);   /* slight-down-right */
  }
  42% {
    opacity: 0.72;
    transform: scale(0.75);
    box-shadow:
       0px -20px  0 1px rgba(180,228,255,0.58),
     -15px -18px  0 1px rgba(180,228,255,0.52),
      15px -18px  0 1px rgba(180,228,255,0.52),
     -22px  -6px  0 1px rgba(175,222,255,0.44),
      22px  -6px  0 1px rgba(175,222,255,0.44),
      -6px -22px  0 0px rgba(180,228,255,0.40),
       6px -22px  0 0px rgba(180,228,255,0.40),
     -18px -14px  0 0px rgba(180,228,255,0.28),
      18px -14px  0 0px rgba(180,228,255,0.28),
      -4px   9px  0 0px rgba(175,222,255,0.18),
       4px   9px  0 0px rgba(175,222,255,0.18);
  }
  100% {
    opacity: 0;
    transform: scale(0.45);
    box-shadow:
       0px -30px  0 0px rgba(180,228,255,0),
     -22px -26px  0 0px rgba(180,228,255,0),
      22px -26px  0 0px rgba(180,228,255,0),
     -32px  -9px  0 0px rgba(175,222,255,0),
      32px  -9px  0 0px rgba(175,222,255,0),
      -9px -32px  0 0px rgba(180,228,255,0),
       9px -32px  0 0px rgba(180,228,255,0),
     -26px -20px  0 0px rgba(180,228,255,0),
      26px -20px  0 0px rgba(180,228,255,0),
      -6px  14px  0 0px rgba(175,222,255,0),
       6px  14px  0 0px rgba(175,222,255,0);
  }
}

/* ── Ripple ring — thin, shallow, compact ───────────────────────────────── */
/* center at ~-1.4×bs above cup center: top = -1.4×bs - (1.2×bs / 2) = -2.0×bs */
.ball-overlay .splash-ring {
  position: absolute;
  left:   calc(var(--bs) * -1.2);
  top:    calc(var(--bs) * -2.0);
  width:  calc(var(--bs) * 2.4);
  height: calc(var(--bs) * 1.2);
  border: 1.5px solid rgba(200, 240, 255, 0.85);
  border-radius: 50%;
  opacity: 0;
  pointer-events: none;
  animation: splash-ring-anim 0.52s ease-out 0.80s forwards;
}

.ball-overlay .splash-ring::after {
  content: '';
  position: absolute;
  inset: -3px;
  border: 1px solid rgba(200, 240, 255, 0.45);
  border-radius: 50%;
  animation: splash-ring-anim 0.60s ease-out 0.87s forwards;
}

@keyframes splash-ring-anim {
  0%   { transform: scale(0.35); opacity: 1.0; }
  25%  {                         opacity: 0.75; }
  100% { transform: scale(1.75); opacity: 0; }
}
</style>
