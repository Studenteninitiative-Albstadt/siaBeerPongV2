<template>
  <!-- Landing -->
  <section v-if="stepProxy === 0" class="text-center py-5">
    <div class="mb-4">
      <h1 class="display-4 fw-bold mb-3">Turnierhalle</h1>
      <p class="text-secondary fs-5 mb-4 mx-auto" style="max-width: 600px;">
        Erstelle in wenigen Schritten ein Beer-Pong-Turnier für euren Verein.
        Das System berechnet automatisch die optimale Gruppenaufteilung.
      </p>
    </div>
    <div class="d-flex justify-content-center gap-3">
      <button class="btn btn-primary btn-lg px-5 py-3" @click="openNameModal">
        Turnier erstellen
      </button>
      <button class="btn btn-outline-light btn-lg px-5 py-3" @click="$emit('open-load-dialog')">
        Turnier laden
      </button>
    </div>
  </section>

  <!-- Schritt 1: Turnierdetails -->
  <section v-else-if="stepProxy === 1" class="mx-auto" style="max-width: 900px;">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">Turnierdetails</h2>
      <p class="text-secondary">Grundlegende Turnierdaten (max. 128 Teams)</p>
    </div>

    <div class="alert alert-info bg-dark border-info text-light">
      <strong>Turniername:</strong> {{ localTournament.name }}
    </div>

    <div class="row g-4 mb-4">
      <div class="col-md-6">
        <label class="form-label fw-semibold">Anzahl Teilnehmer</label>
        <input
          type="number"
          class="form-control form-control-lg bg-dark text-light border-secondary"
          min="2"
          max="128"
          v-model.number="localTournament.participantCount"
          placeholder="z.B. 16"
        />
        <small class="text-light d-block mt-2">
          Automatische Berechnung der optimalen Gruppenaufteilung
        </small>
      </div>

      <div class="col-md-6">
        <label class="form-label fw-semibold">Becher pro Spiel</label>
        <select
          class="form-select form-select-lg bg-dark text-light border-secondary"
          v-model="localTournament.cupsPerGame"
        >
          <option value="6">6 Becher (Short Game)</option>
          <option value="10">10 Becher (Standard)</option>
          <option value="custom">Benutzerdefiniert</option>
        </select>
        <input
          v-if="localTournament.cupsPerGame === 'custom'"
          type="number"
          class="form-control bg-dark text-light border-secondary mt-2"
          min="1"
          max="20"
          v-model.number="localTournament.customCups"
          placeholder="Anzahl Becher"
        />
      </div>

      <div class="col-md-6 mt-4">
        <label class="form-label fw-semibold">Anzahl Tische</label>
        <input
          type="number"
          class="form-control form-control-lg bg-dark text-light border-secondary"
          min="1"
          max="20"
          v-model.number="localTournament.tableCount"
          placeholder="z.B. 2"
        />
        <small class="text-light d-block mt-2">
          Wie viele Spiele können gleichzeitig ausgetragen werden?
        </small>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-4">
      <div class="card-body">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" v-model="localTournament.finaleWith10Cups" id="finale10Cups">
          <label class="form-check-label fw-semibold" for="finale10Cups">Finale mit 10 Bechern spielen</label>
        </div>
        <small class="text-light d-block mt-2">
          Das Finale wird unabhängig von der Gruppenphase immer mit 10 Bechern gespielt
        </small>
      </div>
    </div>

    <div v-if="localTournament.participantCount >= 2" class="mb-4">
      <div class="card bg-dark border-secondary shadow-sm">
        <div class="card-header bg-dark border-bottom border-secondary py-3">
          <h5 class="mb-0 fw-bold text-white">
            Turnierstruktur für {{ localTournament.participantCount }} Teams
          </h5>
        </div>
        <div class="card-body p-4">
          <div class="mb-4">
            <div class="d-flex align-items-center mb-3">
              <span class="badge bg-secondary text-white me-2 px-3 py-2">Gruppenphase</span>
              <span class="text-white">{{ plan.groups.length }} Gruppen</span>
            </div>

            <div class="row g-2 mb-3">
              <div v-for="group in plan.groups" :key="group.name" class="col-6 col-md-4 col-lg-3">
                <div class="card bg-dark border-secondary h-100">
                  <div class="card-body py-2 px-3 text-center">
                    <div class="fw-bold text-white">{{ group.name }}</div>
                    <small class="text-light">{{ group.size }} Teams</small>
                  </div>
                </div>
              </div>
            </div>

            <div class="alert bg-dark border-secondary mb-0">
              <small>
                <strong class="text-white">Weiterkommen:</strong>
                <span class="text-light">Die ersten 2 Teams jeder Gruppe</span>
              </small>
            </div>
          </div>

          <div class="mb-4 pt-3 border-top border-secondary">
            <div class="d-flex align-items-center mb-3">
              <span class="badge bg-secondary text-white me-2 px-3 py-2">KO-Phase</span>
              <span class="text-white">{{ getKoPhaseName(plan.ko_size) }}</span>
            </div>

            <div class="card bg-dark border-secondary">
              <div class="card-body py-2 px-3">
                <div class="d-flex justify-content-between align-items-center">
                  <span class="text-light">{{ plan.ko_size }} Teams</span>
                  <span class="text-white">
                    <span v-if="plan.ko_size === 4">Halbfinale → Finale</span>
                    <span v-else-if="plan.ko_size === 8">Viertelfinale → Halbfinale → Finale</span>
                    <span v-else-if="plan.ko_size === 16">Achtelfinale → Viertelfinale → Halbfinale → Finale</span>
                    <span v-else>Mehrere KO-Runden bis zum Finale</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="plan.playin_needed" class="pt-3 border-top border-secondary">
            <div class="d-flex align-items-center mb-3">
              <span class="badge bg-secondary text-white me-2 px-3 py-2">Play-In Phase</span>
              <span class="text-white">{{ plan.playin_slots_needed }} zusätzliche Plätze</span>
            </div>
            <div class="alert bg-dark border-secondary mb-0">
              <small class="text-white">
                Kandidaten (3./4. je Gruppe) werden nach Becher-Differenz/B+ gerankt; nur Gleichstände am Cut erzeugen Spiele.
              </small>
            </div>
          </div>

          <div v-else class="pt-3 border-top border-secondary">
            <div class="alert bg-dark border-secondary mb-0">
              <small class="text-white">
                <strong>Play-In Phase:</strong>
                <span class="text-light">Nicht benötigt – Alle Teams sind direkt qualifiziert</span>
              </small>
            </div>
          </div>

          <div class="pt-4 mt-4 border-top border-secondary">
            <div class="row g-3 text-center">
              <div class="col-6">
                <div class="card bg-dark border-secondary h-100">
                  <div class="card-body py-3">
                    <div class="display-6 fw-bold text-white mb-1">{{ plan.groups.length }}</div>
                    <small class="text-light">Gruppen</small>
                  </div>
                </div>
              </div>
              <div class="col-6">
                <div class="card bg-dark border-secondary h-100">
                  <div class="card-body py-3">
                    <div class="display-6 fw-bold text-white mb-1">{{ plan.ko_size }}</div>
                    <small class="text-light">KO-Phase</small>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div><!-- /card-body -->
      </div><!-- /card -->
    </div>

    <div class="d-flex justify-content-between mt-5">
      <button class="btn btn-outline-secondary px-4" @click="stepProxy = 0">Zurück</button>
      <button class="btn btn-primary px-5" @click="stepProxy = 2">Weiter</button>
    </div>
  </section>

  <!-- Schritt 2: Teams -->
  <section v-else-if="stepProxy === 2" class="mx-auto" style="max-width: 700px;">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">Teams eingeben</h2>
      <p class="text-secondary">
        Gib Teamnamen und optional die Spielernamen ein. Es werden <strong>{{ localTournament.participantCount }} Teams</strong> erwartet.
      </p>
    </div>

    <form class="card bg-dark border-secondary mb-4" @submit.prevent="addTeam">
      <div class="card-body">
        <div class="row g-2">
          <div class="col-12">
            <input
              v-model="teamInput"
              type="text"
              class="form-control bg-dark text-light border-secondary"
              :class="{ 'border-warning': isTeamInputDisabled }"
              placeholder="Teamname (Pflichtfeld)..."
              :disabled="isTeamInputDisabled"
            />
          </div>
          <div class="col-6">
            <input
              v-model="player1Input"
              type="text"
              class="form-control form-control-sm bg-dark text-light border-secondary"
              placeholder="Spieler 1 (Pflichtfeld)"
              :disabled="isTeamInputDisabled"
            />
          </div>
          <div class="col-6">
            <input
              v-model="player2Input"
              type="text"
              class="form-control form-control-sm bg-dark text-light border-secondary"
              placeholder="Spieler 2 (Pflichtfeld)"
              :disabled="isTeamInputDisabled"
            />
          </div>
          <div class="col-12">
            <button class="btn w-100 px-4" :class="addButtonClass" type="submit" :disabled="!canAddTeam">
              {{ addButtonText }}
            </button>
          </div>
        </div>
        <small v-if="isTeamInputDisabled" class="text-warning mt-2 d-block">
          Maximale Team-Anzahl erreicht. Bitte entferne Teams um weitere hinzuzufügen.
        </small>
      </div>
    </form>

    <div class="card bg-dark border-secondary mb-4">
      <div class="card-header bg-dark border-bottom border-secondary d-flex justify-content-between align-items-center">
        <span class="fw-semibold text-white">Teams ({{ localTeams.length }}/{{ localTournament.participantCount }})</span>
        <span class="badge" :class="statusBadgeClass">{{ localTeams.length }} hinzugefügt</span>
      </div>

      <div class="card-body py-2 border-bottom border-secondary">
        <div class="progress" style="height: 8px;">
          <div
            class="progress-bar"
            :class="progressBarClass"
            :style="{ width: progressPercentage + '%' }"
            role="progressbar"
            :aria-valuenow="progressPercentage"
            aria-valuemin="0"
            aria-valuemax="100"
          ></div>
        </div>
      </div>

      <ul class="list-group list-group-flush">
        <li
          v-for="(t, idx) in localTeams"
          :key="idx"
          class="list-group-item bg-dark text-light border-secondary"
        >
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <span><strong>{{ idx + 1 }}.</strong> {{ t.name }}</span>
              <div v-if="t.player1 || t.player2" class="small text-secondary mt-1">
                <span v-if="t.player1">{{ t.player1 }}</span>
                <span v-if="t.player1 && t.player2"> &amp; </span>
                <span v-if="t.player2">{{ t.player2 }}</span>
              </div>
            </div>
            <button class="btn btn-sm btn-outline-danger ms-2" @click="removeTeam(idx)">Entfernen</button>
          </div>
        </li>

        <li
          v-for="n in emptySlotsCount"
          :key="'empty-' + n"
          class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center"
          style="opacity: 0.6;"
        >
          <span><strong>{{ localTeams.length + n }}.</strong> <em>Platz für Team {{ localTeams.length + n }}</em></span>
          <span class="badge bg-secondary">Noch frei</span>
        </li>

        <li v-if="localTeams.length === 0" class="list-group-item bg-dark text-light text-center border-secondary py-4">
          Noch keine Teams hinzugefügt
        </li>
      </ul>
    </div>

    <div class="alert mb-4" :class="statusAlertClass">
      <div class="d-flex justify-content-between align-items-center">
        <span>{{ validationMessage }}</span>
        <span class="badge" :class="statusBadgeClass">
          {{ localTeams.length }}/{{ localTournament.participantCount }}
        </span>
      </div>
    </div>

    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-secondary px-4" @click="stepProxy = 1">Zurück</button>
      <button class="btn btn-primary px-5" :disabled="!canContinue" @click="stepProxy = 3">
        {{ canContinue ? 'Weiter zur Übersicht' : 'Teams vervollständigen' }}
      </button>
    </div>
  </section>

  <!-- Schritt 3: Übersicht -->
  <section v-else-if="stepProxy === 3" class="mx-auto" style="max-width: 800px;">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">Übersicht</h2>
    </div>

    <div class="card bg-dark border-secondary mb-4 shadow-sm">
      <div class="card-header bg-dark border-bottom border-secondary">
        <h5 class="mb-0 fw-bold text-white">Turniereinstellungen</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6 d-flex justify-content-between">
            <span class="text-light">Teilnehmer:</span>
            <strong class="text-white">{{ localTournament.participantCount }}</strong>
          </div>
          <div class="col-md-6 d-flex justify-content-between">
            <span class="text-light">Becher pro Spiel:</span>
            <strong class="text-white">{{ actualCupsPerGame }}</strong>
          </div>
          <div class="col-md-6" v-if="localTournament.finaleWith10Cups">
            <div class="d-flex justify-content-between">
              <span class="text-light">Finale:</span>
              <strong class="text-warning">10 Becher</strong>
            </div>
          </div>
          <div class="col-md-6 d-flex justify-content-between">
            <span class="text-light">Gruppen:</span>
            <strong class="text-white">{{ plan.groups.length }}</strong>
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-4 shadow-sm">
      <div class="card-header bg-dark border-bottom border-secondary">
        <h5 class="mb-0 fw-bold text-white">Turnierstruktur</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-6">
            <div class="text-light small">Gruppenphase</div>
            <div class="fw-bold text-white">{{ plan.groups.length }} Gruppen</div>
          </div>
          <div class="col-6">
            <div class="text-light small">KO-Phase</div>
            <div class="fw-bold text-white">{{ getKoPhaseName(plan.ko_size) }}</div>
          </div>
          <div class="col-12">
            <div class="text-light small">Play-In</div>
            <div class="fw-bold text-white">
              <span v-if="plan.playin_needed">{{ plan.playin_slots_needed }} Plätze</span>
              <span v-else>Nicht benötigt</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-4 shadow-sm">
      <div class="card-header bg-dark border-bottom border-secondary">
        <h5 class="mb-0 fw-bold text-white">Gruppenaufteilung</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div v-for="group in previewGroups" :key="group.name" class="col-12">
            <div class="card bg-dark border-secondary">
              <div class="card-body py-2">
                <div class="fw-bold text-white mb-1">{{ group.name }}</div>
                <div class="text-light small">{{ group.teams.join(', ') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-secondary px-4" @click="stepProxy = 2">Zurück</button>
      <button class="btn btn-success px-5" @click="emitFinish">Turnier erstellen</button>
    </div>
  </section>

  <!-- Turniernamen-Modal -->
  <div
    class="modal fade"
    id="nameModal"
    tabindex="-1"
    aria-labelledby="nameModalLabel"
    aria-hidden="true"
    ref="nameModalEl"
  >
    <div class="modal-dialog">
      <div class="modal-content bg-dark text-light border border-secondary">
        <div class="modal-header border-secondary">
          <h5 class="modal-title" id="nameModalLabel">Turniername festlegen</h5>
          <button type="button" class="btn-close btn-close-white" @click="closeNameModal" aria-label="Close"></button>
        </div>
        <form @submit.prevent="confirmName">
          <div class="modal-body">
            <label for="tournamentName" class="form-label">Name</label>
            <input
              id="tournamentName"
              ref="nameInputEl"
              type="text"
              class="form-control bg-dark text-light border-secondary"
              v-model.trim="nameInput"
              placeholder="z. B. Vereinscup 2025"
              @keyup.enter="confirmName"
            />
            <div v-if="nameError" class="form-text text-warning mt-2">{{ nameError }}</div>
          </div>
          <div class="modal-footer border-secondary">
            <button type="button" class="btn btn-outline-secondary" @click="closeNameModal">Abbrechen</button>
            <button type="submit" class="btn btn-primary">Weiter</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import { Modal } from 'bootstrap'

/* utils */
const POW2_KO = [4, 8, 16, 32, 64, 128]
const clampInt = (v, min, max) => Math.max(min, Math.min(max, parseInt(v || 0)))
const letters = () => 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
const groupCountByBand = (n) => (n <= 4 ? 1 : n <= 8 ? 2 : n <= 11 ? 3 : n <= 16 ? 4 : Math.max(4, Math.round(n/4.5)))
const balancedSizes = (n, g) => { const b = Math.floor(n/g), r = n%g; return Array.from({length:g}, (_,i)=>b+(i<r?1:0)) }
function computeGroups(n) {
  let g = groupCountByBand(n)
  if (n === 12) return Array.from({length:4}, (_,i)=>({ name:`Gruppe ${letters()[i]}`, size:3 }))
  let sizes = balancedSizes(n, g)
  if (n >= 17) { while (Math.max(...sizes) > 5) { g += 1; sizes = balancedSizes(n, g) } }
  return Array.from({length:g}, (_,i)=>({ name:`Gruppe ${letters()[i]}`, size:sizes[i] }))
}
const chooseKoSize = (qualified) => POW2_KO.find(k => k >= qualified) ?? qualified
function getKoPhaseName(koSize) {
  return koSize === 4 ? 'Halbfinale'
       : koSize === 8 ? 'Viertelfinale'
       : koSize === 16 ? 'Achtelfinale'
       : koSize === 32 ? 'Runde der 32'
       : koSize === 64 ? 'Runde der 64'
       : koSize === 128 ? 'Runde der 128'
       : `KO (${koSize})`
}

/* props/emits */
const props = defineProps({
  step: { type: Number, default: 0 },
  tournament: { type: Object, default: () => ({}) },
  teams: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:step','update:tournament','update:teams','update:team-players','finish','open-load-dialog'])

/* step v-model */
const stepProxy = computed({
  get: () => props.step ?? 0,
  set: (v) => emit('update:step', v),
})

/* state */
function normalizeTournament(input) {
  const t = {
    name: 'Neues Turnier',
    mode: 'groups',
    participantCount: 8,
    cupsPerGame: typeof input?.cupsPerGame === 'number' ? String(input.cupsPerGame) : (input?.cupsPerGame ?? '6'),
    tableCount: input?.tableCount ?? 2,
    finaleWith10Cups: !!input?.finaleWith10Cups,
    customCups: 6,
    ...input,
  }
  if (t.cupsPerGame !== '6' && t.cupsPerGame !== '10' && t.cupsPerGame !== 'custom') {
    t.cupsPerGame = String(t.cupsPerGame || '6')
  }
  return t
}
const localTournament = ref(normalizeTournament(props.tournament))
// localTeams: array of { name, player1, player2 }
const localTeams = ref(
  (props.teams || []).map(t =>
    typeof t === 'string' ? { name: t, player1: '', player2: '' } : { name: t.name || t, player1: t.player1 || '', player2: t.player2 || '' }
  )
)
const teamInput   = ref('')
const player1Input = ref('')
const player2Input = ref('')

/* derived */
const actualCupsPerGame = computed(() =>
  localTournament.value.cupsPerGame === 'custom'
    ? (localTournament.value.customCups || 6)
    : parseInt(localTournament.value.cupsPerGame)
)
const plan = computed(() => {
  const n = clampInt(localTournament.value.participantCount, 2, 128)
  const groups = computeGroups(n)
  const qualified = groups.reduce((acc, g) => acc + Math.min(2, g.size), 0)
  const ko_size = chooseKoSize(qualified)
  const playin_slots_needed = Math.max(0, ko_size - qualified)
  return { groups, ko_size, playin_needed: playin_slots_needed > 0, playin_slots_needed }
})
const previewGroups = computed(() => {
  const groups = []
  const groupCount = plan.value.groups.length
  const teamNames = localTeams.value.length >= localTournament.value.participantCount
    ? localTeams.value.map(t => t.name)
    : Array.from({ length: localTournament.value.participantCount }, (_, i) => `Team ${i + 1}`)
  for (let i = 0; i < groupCount; i++) {
    const groupName = `Gruppe ${String.fromCharCode(65 + i)}`
    const teamsInGroup = []
    for (let j = i; j < teamNames.length; j += groupCount) if (teamNames[j]) teamsInGroup.push(teamNames[j])
    groups.push({ name: groupName, teams: teamsInGroup })
  }
  return groups
})

/* teams ui */
const isTeamInputDisabled = computed(() => localTeams.value.length >= localTournament.value.participantCount)

const canAddTeam = computed(() => {
  if (isTeamInputDisabled.value) return false
  const n = (teamInput.value || '').trim()
  const p1 = (player1Input.value || '').trim()
  const p2 = (player2Input.value || '').trim()
  return n.length > 0 && p1.length > 0 && p2.length > 0
})

const addButtonClass = computed(() => !canAddTeam.value ? 'btn-secondary' : 'btn-primary')
const addButtonText  = computed(() => {
  if (isTeamInputDisabled.value) return 'Maximal erreicht'
  if (!canAddTeam.value) return 'Bitte alle Felder ausfüllen'
  return 'Team hinzufügen'
})

const emptySlotsCount = computed(() => Math.max(0, localTournament.value.participantCount - localTeams.value.length))
const canContinue = computed(() => localTeams.value.length >= localTournament.value.participantCount)
const validationMessage = computed(() => {
  const c = localTeams.value.length, m = localTournament.value.participantCount
  if (c === 0) return 'Bitte füge Teams hinzu um fortzufahren.'
  if (c < m)   return `Noch ${m - c} Team${m - c > 1 ? 's' : ''} benötigt.`
  if (c === m) return 'Perfekt! Alle Teams wurden hinzugefügt.'
  return 'Zu viele Teams - bitte entferne welche.'
})
function _emitTeams() {
  emit('update:teams', localTeams.value.map(t => t.name))
  emit('update:team-players', Object.fromEntries(
    localTeams.value.map(t => [t.name, { player1: t.player1, player2: t.player2 }])
  ))
}
const statusAlertClass = computed(() => {
  const c = localTeams.value.length, m = localTournament.value.participantCount
  if (c === 0) return 'alert-warning bg-dark border-warning'
  if (c < m)   return 'alert-info bg-dark border-info'
  if (c === m) return 'alert-success bg-dark border-success'
  return 'alert-danger bg-dark border-danger'
})
const statusBadgeClass = computed(() => {
  const c = localTeams.value.length, m = localTournament.value.participantCount
  if (c === 0) return 'bg-warning text-dark'
  if (c < m)   return 'bg-info'
  if (c === m) return 'bg-success'
  return 'bg-danger'
})
const progressPercentage = computed(() =>
  Math.max(0, Math.min(100, Math.round((localTeams.value.length / localTournament.value.participantCount) * 100)))
)
const progressBarClass = computed(() => progressPercentage.value < 50 ? 'bg-warning' : (progressPercentage.value < 100 ? 'bg-info' : 'bg-success'))

/* actions */
function addTeam() {
  if (!canAddTeam.value) return
  const name = (teamInput.value || '').trim()
  if (!name) return
  localTeams.value.push({
    name,
    player1: (player1Input.value || '').trim(),
    player2: (player2Input.value || '').trim(),
  })
  teamInput.value = ''
  player1Input.value = ''
  player2Input.value = ''
  _emitTeams()
}
function removeTeam(idx) {
  localTeams.value.splice(idx, 1)
  _emitTeams()
}
async function emitFinish() {
  const finalTournament = {
    name: localTournament.value.name || 'Neues Turnier',
    mode: 'groups',
    participantCount: clampInt(localTournament.value.participantCount, 2, 128),
    cupsPerGame: actualCupsPerGame.value,
    tableCount: clampInt(localTournament.value.tableCount, 1, 20),
    finaleWith10Cups: !!localTournament.value.finaleWith10Cups,
    teams: localTeams.value.map(t => t.name),
    teamPlayers: Object.fromEntries(
      localTeams.value.map(t => [t.name, { player1: t.player1, player2: t.player2 }])
    ),
  }
  emit('finish', finalTournament)
}

/* modal (lazy) */
const nameInput = ref('')
const nameError = ref('')
const nameModalEl = ref(null)
const nameInputEl = ref(null)
let nameModal = null

async function ensureModal() {
  if (!nameModalEl.value) await nextTick()
  if (!nameModal) nameModal = new Modal(nameModalEl.value, { backdrop: 'static', keyboard: false })
}
async function openNameModal() {
  nameInput.value = localTournament.value.name || ''
  nameError.value = ''
  await ensureModal()
  nameModal.show()
  await nextTick(() => nameInputEl.value?.focus())
}
function closeNameModal() { nameModal?.hide() }
function confirmName() {
  const v = (nameInput.value || '').trim()
  if (v.length < 3) {
    nameError.value = 'Bitte mindestens 3 Zeichen eingeben.'
    nextTick(() => nameInputEl.value?.focus())
    return
  }
  localTournament.value.name = v
  emit('update:tournament', { ...localTournament.value })
  closeNameModal()
  stepProxy.value = 1
}
</script>
