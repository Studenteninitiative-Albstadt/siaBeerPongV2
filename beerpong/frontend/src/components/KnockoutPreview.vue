<template>
  <section class="mx-auto knockout-preview">
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
      <div>
        <h2 class="mb-1">KO-Vorschau</h2>
        <p class="mb-0 text-secondary small">
          Vorschau der KO-Slots mit Qualifikationswegen vor dem Start der Finalrunde.
        </p>
      </div>
      <button class="btn btn-outline-light" @click="$emit('cancel')">Zurück</button>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-4">
        <div class="card bg-dark border-secondary h-100">
          <div class="card-body">
            <div class="small text-secondary mb-1">Teilnehmende Teams</div>
            <div class="display-6 fw-bold text-white">{{ teams.length }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-dark border-secondary h-100">
          <div class="card-body">
            <div class="small text-secondary mb-1">KO-Größe</div>
            <div class="display-6 fw-bold text-white">{{ resolvedKoSize }}</div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card bg-dark border-secondary h-100">
          <div class="card-body">
            <div class="small text-secondary mb-1">Belegung</div>
            <div class="display-6 fw-bold text-white">{{ normalizedSlots.length }}/{{ resolvedKoSize }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-4">
      <div class="card-header bg-dark border-secondary d-flex justify-content-between align-items-center flex-wrap gap-2">
        <strong>Turnierbaum</strong>
        <span class="small text-secondary">Platzhalter wie Sieger Gruppe A oder Sieger Play-In bleiben bis zum KO-Start sichtbar.</span>
      </div>
      <div class="card-body p-0">
        <KnockoutPreviewTree :slots="normalizedSlots" :ko-size="resolvedKoSize" />
      </div>
    </div>

    <div class="card bg-dark border-secondary">
      <div class="card-header bg-dark border-secondary">
        <strong>Startfelder</strong>
      </div>
      <div class="card-body">
        <div v-if="normalizedSlots.length" class="slot-list">
          <article
            v-for="slot in normalizedSlots"
            :key="slot.id"
            class="slot-list__item"
          >
            <div class="slot-list__label">{{ slot.sourceLabel }}</div>
            <div class="slot-list__team">{{ slot.teamName || 'Noch offen' }}</div>
          </article>
        </div>
        <div v-else class="text-secondary small">
          Noch keine Teams für die KO-Phase vorhanden.
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-between mt-4 flex-wrap gap-2">
      <button class="btn btn-outline-light" @click="$emit('cancel')">Zurück</button>
      <button class="btn btn-success" @click="confirm">KO-Phase starten</button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import KnockoutPreviewTree from './KnockoutPreviewTree.vue'

const POW2 = [4, 8, 16, 32, 64, 128]

const props = defineProps({
  teams: { type: Array, default: () => [] },
  koSize: { type: Number, default: null },
  slots: { type: Array, default: () => [] },
})

const emit = defineEmits(['confirm', 'cancel'])

const resolvedKoSize = computed(() => {
  if (props.koSize) return props.koSize
  const n = props.teams.length || props.slots.length
  for (const k of POW2) if (k >= n) return k
  return Math.max(4, n)
})

const normalizedSlots = computed(() => {
  const explicitSlots = (props.slots || [])
    .map((slot, idx) => normalizeSlot(slot, idx))
    .filter(Boolean)

  if (explicitSlots.length) return explicitSlots

  return (props.teams || [])
    .filter(Boolean)
    .map((team, idx) => ({
      id: `team-${idx}`,
      sourceLabel: `Team ${idx + 1}`,
      teamName: team,
    }))
})

function normalizeSlot(slot, idx) {
  if (!slot) return null
  if (typeof slot === 'string') {
    return {
      id: `slot-${idx}`,
      sourceLabel: slot,
      teamName: slot,
    }
  }
  return {
    id: slot.id ?? `slot-${idx}`,
    sourceLabel: slot.sourceLabel || slot.label || slot.teamName || slot.team || `Slot ${idx + 1}`,
    teamName: slot.teamName || slot.team || '',
  }
}

function confirm() {
  emit('confirm', { teams: props.teams.slice(), koSize: resolvedKoSize.value })
}
</script>

<style scoped>
.knockout-preview {
  max-width: 1320px;
}

.slot-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.9rem;
}

.slot-list__item {
  padding: 0.9rem 1rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.slot-list__label {
  color: #ffffff;
  font-weight: 700;
  line-height: 1.2;
}

.slot-list__team {
  margin-top: 0.35rem;
  color: rgba(255, 255, 255, 0.62);
  font-size: 0.9rem;
  line-height: 1.25;
}
</style>
