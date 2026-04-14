<template>
  <div class="ko-bracket w-100">
    <!-- Horizontales Scrollen für alle Runden -->
    <div class="rounds-scroll">
      <!-- Alle normalen Runden außer Finale -->
      <div
        v-for="info in mainExceptFinalInfos"
        :key="'main-' + info.idx"
        class="round-column"
      >
        <div class="round-header">
          <span class="round-title">
            {{ info.r.round_name || defaultRoundName(info.localIndex, mainInfos.length) }}
          </span>
        </div>

        <div class="round-body">
          <div
            v-for="(m, mIdx) in info.r.matches"
            :key="mIdx"
            class="match-card"
          >
            <div class="match-header">
              <span class="match-label">Spiel {{ mIdx + 1 }}</span>
              <span v-if="activeMatchIds?.has(m.id)" class="ko-live-pulse"></span>
            </div>

            <div class="match-body">
              <!-- Team 1 -->
              <div class="team-row">
                <button
                  class="btn btn-sm team-btn text-start text-truncate"
                  :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                  disabled
                >
                  {{ m.team1 || '—' }}
                </button>

                <div
                  v-if="interactive"
                  class="score-controls"
                >
                  
                  <input
                    type="number"
                    class="form-control form-control-sm cups-input text-center fw-bold"
                    :value="safeNum(m.cups_team1)"
                    @input="onSetCups(info.idx, mIdx, 'team1', $event.target.value)"
                    min="0"
                    :max="cupsTargetFn(info.idx)"
                    :disabled="!m.team1 || readonly"
                  />
                  <button
                    class="btn btn-sm p-1 lh-1 score-btn"
                    :class="m.team1 ? 'btn-outline-light hover-scale' : 'btn-outline-secondary disabled'"
                    @click="onIncrementCup(info.idx, mIdx, 'team1')"
                    :disabled="!m.team1 || readonly"
                  >
                    <img src="/beer-cup.svg" alt="Cup" width="18" height="18" />
                  </button>
                </div>
              </div>

              <!-- Trenner -->
              <div class="vs-row">
                <span class="vs-text">vs</span>
              </div>

              <!-- Team 2 -->
              <div class="team-row">
                <button
                  class="btn btn-sm team-btn text-start text-truncate"
                  :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                  disabled
                >
                  {{ m.team2 || '—' }}
                </button>

                <div
                  v-if="interactive"
                  class="score-controls"
                >
                  <input
                    type="number"
                    class="form-control form-control-sm cups-input text-center fw-bold"
                    :value="safeNum(m.cups_team2)"
                    @input="onSetCups(info.idx, mIdx, 'team2', $event.target.value)"
                    min="0"
                    :max="cupsTargetFn(info.idx)"
                    :disabled="!m.team2 || readonly"
                  />
                  <button
                    class="btn btn-sm p-1 lh-1 score-btn"
                    :class="m.team2 ? 'btn-outline-light hover-scale' : 'btn-outline-secondary disabled'"
                    @click="onIncrementCup(info.idx, mIdx, 'team2')"
                    :disabled="!m.team2 || readonly"
                  >
                    <img src="/beer-cup.svg" alt="Cup" width="18" height="18" />
                  </button>
                </div>
              </div>
            </div>

            <div class="match-footer">
              <small v-if="m.winner" class="text-success">
                Sieger: {{ m.winner }}
              </small>
              <small v-else class="text-light opacity-75">
                Sieger wird über Becher entschieden
              </small>
            </div>
          </div>

          <div v-if="!info.r.matches?.length" class="text-light small text-center opacity-75">
            Keine Spiele in dieser Runde
          </div>
        </div>
      </div>

      <!-- Finale + Spiel um Platz 3 als eigene "Finalrunde"-Spalte -->
      <div
        v-if="placementInfo || finalInfo"
        class="round-column"
      >
        <div class="round-header">
          <span class="round-title">Finalrunde</span>
        </div>

        <div class="round-body">
          <!-- Spiel um Platz 3 -->
          <div
            v-if="placementInfo"
            class="final-section"
          >
            <div class="final-section-header">
              <span class="final-section-title">Spiel um Platz 3</span>
            </div>

            <div
              v-for="(m, mIdx) in placementInfo.r.matches"
              :key="'p-' + mIdx"
              class="match-card"
            >
              <div class="match-header">
                <span class="match-label">Platz 3</span>
                <span v-if="activeMatchIds?.has(m.id)" class="ko-live-pulse"></span>
              </div>

              <div class="match-body">
                <!-- Team 1 -->
                <div class="team-row">
                  <button
                    class="btn btn-sm team-btn text-start text-truncate"
                    :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                    disabled
                  >
                    {{ m.team1 || '—' }}
                  </button>

                  <div
                    v-if="interactive"
                    class="score-controls"
                  >
                    
                    <input
                      type="number"
                      class="form-control form-control-sm cups-input text-center fw-bold"
                      :value="safeNum(m.cups_team1)"
                      @input="onSetCups(placementInfo.idx, mIdx, 'team1', $event.target.value)"
                      min="0"
                      :max="cupsTargetFn(placementInfo.idx)"
                      :disabled="!m.team1 || readonly"
                    />
                    <button
                      class="btn btn-sm p-1 lh-1 score-btn"
                      :class="m.team1 ? 'btn-outline-light hover-scale' : 'btn-outline-secondary disabled'"
                      @click="onIncrementCup(placementInfo.idx, mIdx, 'team1')"
                      :disabled="!m.team1 || readonly"
                    >
                      <img src="/beer-cup.svg" alt="Cup" width="18" height="18" />
                    </button>
                  </div>
                </div>

                <!-- Trenner -->
                <div class="vs-row">
                  <span class="vs-text">vs</span>
                </div>

                <!-- Team 2 -->
                <div class="team-row">
                  <button
                    class="btn btn-sm team-btn text-start text-truncate"
                    :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                    disabled
                  >
                    {{ m.team2 || '—' }}
                  </button>

                  <div
                    v-if="interactive"
                    class="score-controls"
                  >
                    <input
                      type="number"
                      class="form-control form-control-sm cups-input text-center fw-bold"
                      :value="safeNum(m.cups_team2)"
                      @input="onSetCups(placementInfo.idx, mIdx, 'team2', $event.target.value)"
                      min="0"
                      :max="cupsTargetFn(placementInfo.idx)"
                      :disabled="!m.team2 || readonly"
                    />
                    <button
                      class="btn btn-sm p-1 lh-1 score-btn"
                      :class="m.team2 ? 'btn-outline-light hover-scale' : 'btn-outline-secondary disabled'"
                      @click="onIncrementCup(placementInfo.idx, mIdx, 'team2')"
                      :disabled="!m.team2 || readonly"
                    >
                      <img src="/beer-cup.svg" alt="Cup" width="18" height="18" />
                    </button>
                  </div>
                </div>
              </div>

              <div class="match-footer">
                <small v-if="m.winner" class="text-success">
                  Sieger: {{ m.winner }}
                </small>
                <small v-else class="text-light opacity-75">
                  Sieger wird über Becher entschieden
                </small>
              </div>
            </div>
          </div>

          <!-- Finale -->
          <div
            v-if="finalInfo"
            class="final-section mt-3"
          >
            <div class="final-section-header">
              <span class="final-section-title">Finale</span>
            </div>

            <div
              v-for="(m, mIdx) in finalInfo.r.matches"
              :key="'f-' + mIdx"
              class="match-card"
            >
              <div class="match-header">
                <span class="match-label">Finale</span>
                <span v-if="activeMatchIds?.has(m.id)" class="ko-live-pulse"></span>
              </div>

              <div class="match-body">
                <!-- Team 1 -->
                <div class="team-row">
                  <button
                    class="btn btn-sm team-btn text-start text-truncate"
                    :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                    disabled
                  >
                    {{ m.team1 || '—' }}
                  </button>

                  <div
                    v-if="interactive"
                    class="score-controls"
                  >
                    
                    <input
                      type="number"
                      class="form-control form-control-sm cups-input text-center fw-bold"
                      :value="safeNum(m.cups_team1)"
                      @input="onSetCups(finalInfo.idx, mIdx, 'team1', $event.target.value)"
                      min="0"
                      :max="cupsTargetFn(finalInfo.idx)"
                      :disabled="!m.team1 || readonly"
                    />
                    <button
                      class="btn btn-sm p-1 lh-1 score-btn"
                      :class="m.team1 ? 'btn-outline-light hover-scale' : 'btn-outline-secondary disabled'"
                      @click="onIncrementCup(finalInfo.idx, mIdx, 'team1')"
                      :disabled="!m.team1 || readonly"
                    >
                      <img src="/beer-cup.svg" alt="Cup" width="18" height="18" />
                    </button>
                  </div>
                </div>

                <!-- Trenner -->
                <div class="vs-row">
                  <span class="vs-text">vs</span>
                </div>

                <!-- Team 2 -->
                <div class="team-row">
                  <button
                    class="btn btn-sm team-btn text-start text-truncate"
                    :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                    disabled
                  >
                    {{ m.team2 || '—' }}
                  </button>

                  <div
                    v-if="interactive"
                    class="score-controls"
                  >
                    <input
                      type="number"
                      class="form-control form-control-sm cups-input text-center fw-bold"
                      :value="safeNum(m.cups_team2)"
                      @input="onSetCups(finalInfo.idx, mIdx, 'team2', $event.target.value)"
                      min="0"
                      :max="cupsTargetFn(finalInfo.idx)"
                      :disabled="!m.team2 || readonly"
                    />
                    <button
                      class="btn btn-sm p-1 lh-1 score-btn"
                      :class="m.team2 ? 'btn-outline-light hover-scale' : 'btn-outline-secondary disabled'"
                      @click="onIncrementCup(finalInfo.idx, mIdx, 'team2')"
                      :disabled="!m.team2 || readonly"
                    >
                      <img src="/beer-cup.svg" alt="Cup" width="18" height="18" />
                    </button>
                  </div>
                </div>
              </div>

              <div class="match-footer">
                <small v-if="m.winner" class="text-success">
                  Sieger: {{ m.winner }}
                </small>
                <small v-else class="text-light opacity-75">
                  Sieger wird über Becher entschieden
                </small>
              </div>
            </div>
          </div>

          <div
            v-if="!(placementInfo && placementInfo.r.matches?.length) && !(finalInfo && finalInfo.r.matches?.length)"
            class="text-light small text-center opacity-75"
          >
            Keine Spiele in dieser Runde
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rounds: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
  interactive: { type: Boolean, default: false },
  cupsTargetFn: {
    type: Function,
    default: () => 6
  },
  activeMatchIds: { type: Object, default: null } // Set<number>
})

const emit = defineEmits(['increment-cup', 'set-cups'])

function defaultRoundName(idx, total) {
  const map = ['Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale']
  const fromEnd = total - idx
  return map[fromEnd - 1] || `Runde ${idx + 1}`
}

function safeNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function onIncrementCup(rIdx, mIdx, team) {
  if (props.readonly) return
  emit('increment-cup', { roundIndex: rIdx, matchIndex: mIdx, team })
}

function onSetCups(rIdx, mIdx, team, value) {
  if (props.readonly) return
  emit('set-cups', { roundIndex: rIdx, matchIndex: mIdx, team, value })
}

/* Rundeninfos vorbereiten */
const mainInfos = computed(() =>
  props.rounds
    .map((r, idx) => ({ r, idx }))
    .filter(x => x.r.bracket_type !== 'placement')
    .map((x, localIndex) => ({ ...x, localIndex }))
)

const finalInfo = computed(() => {
  if (!mainInfos.value.length) return null
  return mainInfos.value[mainInfos.value.length - 1]
})

const mainExceptFinalInfos = computed(() => {
  const fIdx = finalInfo.value?.idx
  return mainInfos.value.filter(x => x.idx !== fIdx)
})

const placementInfo = computed(() => {
  const idx = props.rounds.findIndex(r => r.bracket_type === 'placement')
  if (idx === -1) return null
  return { r: props.rounds[idx], idx }
})

/* HMR deaktivieren */
if (import.meta && import.meta.hot) {
  import.meta.hot.decline()
}
</script>

<style scoped>
.ko-bracket {
  width: 100%;
}

/* Horizontales Scrolling über alle Runden-Spalten */
.rounds-scroll {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: visible;
  gap: 1.25rem;
  padding-bottom: 0.5rem;
}

/* Spalte für eine Runde */
.round-column {
  min-width: 260px;
  max-width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

/* Rundenkopf */
.round-header {
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  background: linear-gradient(135deg, #1f2630, #15181c);
  border: 1px solid rgba(108, 117, 125, 0.75);
  margin-bottom: 0.6rem;
}
.round-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #f8f9fa;
}

/* Rundencolumn-Body */
.round-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Match-Karte als losgelöstes Element */
.match-card {
  background: radial-gradient(circle at top left, rgba(255, 255, 255, 0.03), rgba(0, 0, 0, 0.9));
  border-radius: 14px;
  border: 1px solid rgba(73, 80, 87, 0.9);
  padding: 0.6rem 0.75rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.35);
}

/* Kopf der Match-Karte */
.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}
.match-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #adb5bd;
}

.ko-live-pulse {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #dc3545;
  flex-shrink: 0;
  animation: ko-pulse 1.2s ease-in-out infinite;
}

@keyframes ko-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); opacity: 1; }
  50%       { box-shadow: 0 0 0 6px rgba(220, 53, 69, 0);  opacity: 0.8; }
}

/* Inhalt der Match-Karte */
.match-body {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

/* Team-Zeile */
.team-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Button für Teamname */
.team-btn {
  flex: 1 1 auto;
}

/* Score-Controls (Becher) */
.score-controls {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

/* Input für Becher */
.cups-input {
  width: 52px;
  background: rgba(0, 0, 0, 0.6);
  border: 2px solid #495057;
  color: #ffc107;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.cups-input:focus {
  border-color: #ffc107;
  box-shadow: 0 0 0 0.15rem rgba(255, 193, 7, 0.25);
}

/* Cup-Button */
.score-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* "vs"-Zeile */
.vs-row {
  display: flex;
  justify-content: center;
  align-items: center;
}
.vs-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #adb5bd;
}

/* Footer der Match-Karte */
.match-footer {
  margin-top: 0.3rem;
  border-top: 1px dashed rgba(108, 117, 125, 0.6);
  padding-top: 0.3rem;
}

/* Final-Abschnitte */
.final-section-header {
  margin-bottom: 0.25rem;
}
.final-section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #f8f9fa;
}

/* Hover / Visuelles Feedback */
.hover-scale:hover {
  transform: scale(1.05);
}

/* Karten-Shadow-Hover leicht verstärken */
.match-card:hover {
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.5);
}

/* Scrollbar-Optik für horizontales Scrolling */
.rounds-scroll::-webkit-scrollbar {
  height: 8px;
}
.rounds-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.rounds-scroll::-webkit-scrollbar-thumb {
  background: rgba(108, 117, 125, 0.8);
  border-radius: 999px;
}
.rounds-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(108, 117, 125, 1);
}
</style>
