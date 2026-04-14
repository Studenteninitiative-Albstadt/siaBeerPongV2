<template>
  <section class="mx-auto" style="max-width: 1200px;">
    <!-- Kopf -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="mb-1">Play-In Phase</h2>
        <p class="mb-0 text-secondary small">
          Entscheide die letzten Startplätze für die KO-Phase.
        </p>
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-light btn-sm" @click="$emit('back')">
          Zurück zur Gruppenphase
        </button>
      </div>
    </div>

    <div class="row g-4">
      <!-- Linke Spalte: Qualifizierte, Kandidaten -->
      <div class="col-lg-5">
        <!-- Direkt qualifiziert -->
        <div class="card bg-dark border-secondary mb-3">
          <div class="card-header bg-dark border-secondary">
            <strong>Direkt qualifiziert</strong>
          </div>
          <div class="card-body">
            <div v-if="autoQualifiedComputed.length" class="d-flex flex-wrap gap-2">
              <span
                v-for="t in autoQualifiedComputed"
                :key="t"
                class="badge bg-success"
              >
                {{ t }}
              </span>
            </div>
            <div v-else class="text-secondary small">
              Noch keine direkt qualifizierten Teams.
            </div>
          </div>
        </div>

        <!-- Ranking-Kandidaten -->
        <div class="card bg-dark border-secondary mb-3" v-if="candidatesComputed.length">
          <div class="card-header bg-dark border-secondary">
            <strong>Ranking-Kandidaten</strong>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-dark table-striped mb-0 small">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Team</th>
                    <th class="text-center">P</th>
                    <th class="text-center">±</th>
                    <th class="text-center">B+</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(c, idx) in candidatesComputed"
                    :key="c.name + idx"
                  >
                    <td>{{ idx + 1 }}</td>
                    <td>{{ c.name }}</td>
                    <td class="text-center">{{ c.points }}</td>
                    <td
                      class="text-center"
                      :class="{
                        'text-success': c.cupsDiff > 0,
                        'text-danger': c.cupsDiff < 0
                      }"
                    >
                      {{ c.cupsDiff > 0 ? '+' : '' }}{{ c.cupsDiff }}
                    </td>
                    <td class="text-center">{{ c.cupsFor }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Rage-Cage Info -->
        <div
          v-if="rageCageComputed.length"
          class="card bg-dark border-warning mb-3"
        >
          <div class="card-header bg-dark border-warning text-warning">
            <strong>Rage-Cage Konstellationen</strong>
          </div>
          <div class="card-body">
            <div
              v-for="(rc, idx) in rageCageComputed"
              :key="idx"
              class="mb-3"
            >
              <div class="text-warning small mb-1">
                Gruppe / Bereich: {{ rc.group || 'Cut-Off' }}
              </div>
              <div class="d-flex flex-wrap gap-1 mb-1">
                <span
                  v-for="t in rc.teams"
                  :key="t"
                  class="badge bg-secondary"
                >
                  {{ t }}
                </span>
              </div>
              <div class="text-secondary small" v-if="rc.note">
                {{ rc.note }}
              </div>
            </div>
            <div class="text-secondary small">
              Rage-Cage wird in der Praxis ausgespielt; Ergebnis bitte bei der
              KO-Planung berücksichtigen.
            </div>
          </div>
        </div>

        <!-- Policy Notes -->
        <div v-if="policyNotesComputed.length" class="card bg-dark border-secondary">
          <div class="card-header bg-dark border-secondary">
            <strong>Hinweise</strong>
          </div>
          <div class="card-body">
            <ul class="mb-0 small text-secondary">
              <li v-for="(n, i) in policyNotesComputed" :key="i">
                {{ n }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Rechte Spalte: Play-In Matches -->
      <div class="col-lg-7">
        <div class="card bg-dark border-secondary h-100 d-flex flex-column">
          <div class="card-header bg-dark border-secondary d-flex justify-content-between align-items-center">
            <strong>Play-In Matches</strong>
            <small class="text-secondary">
              KO-Zielgröße:
              <span class="text-light fw-semibold">
                {{ koSizeComputed }} Teams
              </span>
            </small>
          </div>

          <div class="card-body">
            <!-- Wenn keine Matches -->
            <div v-if="!localMatches.length" class="text-secondary">
              Momentan sind keine Play-In-Spiele definiert.
              <br />
              Falls Rage-Cage/Elfmeter o.ä. offline gespielt wird, kannst du danach direkt zur KO-Phase weitergehen
              und die Teams dort manuell justieren.
            </div>

            <!-- Matches-Liste -->
            <div v-else class="d-flex flex-column gap-3">
              <div
                v-for="(m, idx) in localMatches"
                :key="m.id || idx"
                class="playin-match border border-secondary rounded p-3"
              >
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <div class="small text-secondary">
                    Match {{ idx + 1 }}
                    <span v-if="m.cups_per_game" class="ms-2 badge bg-dark border border-secondary">
                      {{ m.cups_per_game }} Becher
                    </span>
                  </div>
                  <div class="small text-secondary">
                    Sieger auswählen
                  </div>
                </div>

                <div class="d-flex align-items-center justify-content-between gap-2">
                  <!-- Team 1 -->
                  <button
                    class="btn btn-sm flex-grow-1 text-truncate"
                    :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                    @click="selectWinner(idx, 'team1')"
                    :title="m.team1"
                  >
                    {{ m.team1 }}
                  </button>

                  <span class="text-secondary mx-2">vs</span>

                  <!-- Team 2 -->
                  <button
                    class="btn btn-sm flex-grow-1 text-truncate"
                    :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                    @click="selectWinner(idx, 'team2')"
                    :title="m.team2"
                  >
                    {{ m.team2 }}
                  </button>
                </div>

                <div class="mt-2 small text-secondary" v-if="m.winner">
                  Sieger: <span class="text-success fw-semibold">{{ m.winner }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card-footer bg-dark border-secondary d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
            <div class="small text-secondary">
              <div>
                Bisher qualifiziert für KO:
                <span v-if="finalQualified.length" class="text-light fw-semibold">
                  {{ finalQualified.length }} Teams
                </span>
                <span v-else class="text-warning">Noch keine vollständige Liste.</span>
              </div>
              <div v-if="finalQualified.length" class="mt-1">
                <span class="badge bg-secondary me-1" v-for="t in finalQualified" :key="t">
                  {{ t }}
                </span>
              </div>
            </div>

            <div class="d-flex gap-2 justify-content-end">
              <button class="btn btn-outline-light" @click="$emit('back')">
                Zurück
              </button>
              <button
                class="btn btn-success"
                :disabled="!canContinueToKo"
                @click="confirmAndGoToKo"
              >
                Weiter zur KO-Phase
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  tournamentId: { type: Number, required: true },
  autoQualified: { type: Array, default: () => [] },    // pendingQualified aus App.vue
  autoQualifiedSlots: { type: Array, default: () => [] },
  koSize: { type: Number, default: null },              // targetKoSize aus App.vue (pi.ko_size)
  candidates: { type: Array, default: () => [] },       // playInCandidates (ranking_candidates)
  matches: { type: Array, default: () => [] },          // playInMatches (playin_matches)
  rageCage: { type: Array, default: () => [] },         // rage_cage_groups
  policyNotes: { type: Array, default: () => [] }       // policy_notes
})

const emit = defineEmits(['back', 'to-ko', 'create-ko'])

const API =
  `${window.location.protocol}//${window.location.hostname}:5001` ||
  import.meta.env.VITE_API_BASE

/* ---------- State ---------- */

const localMatches = ref((props.matches || []).map(normalizeMatch))

watch(
  () => props.matches,
  (val) => {
    localMatches.value = (val || []).map(normalizeMatch)
  },
  { deep: true }
)

/* ---------- Computed ---------- */

const autoQualifiedComputed = computed(
  () => props.autoQualified?.slice() ?? []
)

const autoQualifiedSlotsComputed = computed(
  () => props.autoQualifiedSlots?.slice() ?? []
)

const candidatesComputed = computed(
  () => props.candidates?.slice() ?? []
)

const rageCageComputed = computed(
  () => props.rageCage?.slice() ?? []
)

const policyNotesComputed = computed(
  () => props.policyNotes?.slice() ?? []
)

// Gewinner aus den Play-In-Matches
const playInWinners = computed(() =>
  localMatches.value
    .filter(m => m.winner)
    .map(m => m.winner)
)

// Finale KO-Liste = Direktqualifizierte + Play-In-Sieger (Duplikate entfernt)
const finalQualified = computed(() => {
  const result = []
  const seen = new Set()

  for (const t of autoQualifiedComputed.value) {
    if (t && !seen.has(t)) {
      seen.add(t)
      result.push(t)
    }
  }

  for (const w of playInWinners.value) {
    if (w && !seen.has(w)) {
      seen.add(w)
      result.push(w)
    }
  }

  // Falls eine KO-Größe vorgegeben ist, hard-limit
  if (props.koSize && result.length > props.koSize) {
    return result.slice(0, props.koSize)
  }
  return result
})

function pow2KoSize(n) {
  const sizes = [4, 8, 16, 32, 64, 128]
  for (const k of sizes) if (k >= n) return k
  return n
}

const koSizeComputed = computed(() => {
  const n = finalQualified.value.length
  if (props.koSize) return props.koSize
  if (n <= 0) return 0
  return pow2KoSize(n)
})

// Button nur aktiv, wenn entweder
// - keine Matches definiert sind (Edge Case, z.B. nur Rage-Cage offline)
// - oder alle Matches einen Sieger haben
const allMatchesHaveWinner = computed(() => {
  if (!localMatches.value.length) return true
  return localMatches.value.every(m => !!m.winner)
})

const canContinueToKo = computed(() =>
  finalQualified.value.length > 0 && allMatchesHaveWinner.value
)

/* ---------- Helpers ---------- */

function normalizeMatch(m) {
  return {
    id: m.id ?? null,
    team1: m.team1 ?? '',
    team2: m.team2 ?? '',
    winner: m.winner ?? null,
    cups_per_game: m.cups_per_game ?? m.cupsPerGame ?? null
  }
}

function selectWinner(matchIndex, teamKey) {
  const list = [...localMatches.value]
  const m = { ...list[matchIndex] }
  if (!m.team1 || !m.team2) return

  m.winner = teamKey === 'team1' ? m.team1 : m.team2
  list[matchIndex] = m
  localMatches.value = list
}

/* ---------- Hauptaktion: Weiter zur KO-Phase ---------- */

async function confirmAndGoToKo() {
  const qualified = finalQualified.value
  const koSize = koSizeComputed.value
  const previewSlots = localMatches.value
    .map((match, idx) => {
      if (!match.winner) return null
      return {
        id: `playin-slot-${match.id ?? idx}`,
        sourceLabel: `Sieger Play-In ${idx + 1}`,
        teamName: match.winner
      }
    })
    .filter(Boolean)

  const payload = {
    // für App.vue / KO-Preview:
    koSize,
    qualified,
    previewSlots,

    // für persistenten "Übertrag" aus der Tabellenlogik:
    ko_size: koSize,                                // 👈 wichtig für load-all-data
    direct_qualified: autoQualifiedComputed.value,
    direct_qualified_slots: autoQualifiedSlotsComputed.value,
    playin_matches: localMatches.value,
    rage_cage_groups: rageCageComputed.value,
    policy_notes: policyNotesComputed.value,
    ranking_candidates: candidatesComputed.value
  }

  // In DB persistieren (save-playin) – Backend speichert alles 1:1
  if (props.tournamentId) {
    try {
      await fetch(`${API}/tournaments/${props.tournamentId}/save-playin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    } catch (e) {
      console.error('save-playin failed', e)
      // optional: UI-Feedback
    }
  }

  // An App.vue übergeben – handlePlayInToKo nutzt qualified + koSize
  emit('to-ko', payload)
  // optionaler Alias für ältere Aufrufer
  emit('create-ko', payload)
}
</script>

<style scoped>
.playin-match {
  background: rgba(255, 255, 255, 0.03);
}

.playin-match:hover {
  background: rgba(255, 255, 255, 0.06);
}

.card.bg-dark {
  color: #f8f9fa;
}

.card-header.bg-dark {
  color: #f8f9fa;
}

.btn-outline-light {
  border-color: #ced4da;
}

.btn-outline-light:hover {
  background-color: #f8f9fa;
  color: #000;
}
</style>
