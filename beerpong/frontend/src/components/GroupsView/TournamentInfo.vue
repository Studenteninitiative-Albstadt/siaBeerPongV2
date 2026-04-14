<template>
  <div class="card bg-dark border-secondary mb-3">
    <div class="card-body">
      <div class="row g-3 align-items-center">
        <div class="col-md">
          <div class="d-flex align-items-center gap-4 flex-wrap">
            <div>
              <div class="text-light small">Teilnehmer</div>
              <div class="h4 mb-0 text-white">
                {{ participants }}
              </div>
            </div>
            <div>
              <div class="text-light small">Becher / Spiel</div>
              <div class="h4 mb-0 text-white">
                {{ cupsPerGame }}
              </div>
            </div>
            <div>
              <div class="text-light small">Phase</div>
              <div class="h4 mb-0 text-white">
                {{ phase }}
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-auto">
          <!-- Button entfernt, da automatisch -->
        </div>
      </div>

      <div v-if="autoGroupsPreview?.length" class="mt-3">
        <div class="text-light small mb-1">Vorschau Gruppenaufteilung</div>
        <div class="row g-2">
          <div
            v-for="g in autoGroupsPreview"
            :key="g.name"
            class="col-12 col-md-6 col-lg-4"
          >
            <div class="card bg-dark border-secondary h-100">
              <div class="card-body py-2">
                <div class="fw-bold text-white">{{ g.name }}</div>
                <div class="text-light small">
                  {{ (g.teams && g.teams.length) ? g.teams.join(', ') : '—' }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="!autoGroupsPreview.length" class="col-12 text-light small">
            Keine Vorschau verfügbar.
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tournament: { type: Object, required: true },
  autoGroupsPreview: { type: Array, default: () => [] },
  // Optional: Teams-Liste, damit der Button nicht klickbar ist, wenn <2 Teams
  teams: { type: Array, default: () => [] }
})
defineEmits(['generate'])

const participants = computed(() =>
  props.tournament?.participant_count ??
  props.tournament?.participantCount ??
  '–'
)

const cupsPerGame = computed(() =>
  props.tournament?.cups_per_game ??
  props.tournament?.cupsPerGame ??
  6
)

const phase = computed(() =>
  props.tournament?.current_phase ??
  props.tournament?.currentPhase ??
  'group'
)

const canGenerate = computed(() => (props.teams?.length ?? 0) >= 2)
</script>

<style scoped>
.card { transition: all .2s ease; }
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.25); }
</style>
