<template>
  <div class="min-vh-100 bg-dark text-light"
       style="background:radial-gradient(circle at top,#0d1b2a 0%,#0a0a0a 60%,#000 100%)">

    <!-- Invalid / Loading -->
    <div v-if="!valid && !loading"
         class="min-vh-100 d-flex align-items-center justify-content-center p-4">
      <div class="text-center">
        <div class="fs-1 mb-3">🚫</div>
        <h4 class="text-danger">Ungültiger Zugangslink</h4>
        <p class="text-secondary small">Scanne den QR-Code erneut am Beamer.</p>
      </div>
    </div>

    <div v-else-if="loading"
         class="min-vh-100 d-flex align-items-center justify-content-center">
      <div class="spinner-border text-light" role="status"></div>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="bg-black border-bottom border-secondary py-3 px-4 d-flex justify-content-between align-items-center">
        <span class="fw-bold">🍺 {{ tournament?.name }}</span>
        <span class="badge" :class="wsConnected ? 'bg-success' : 'bg-secondary'">
          {{ wsConnected ? '● Live' : '○ Offline' }}
        </span>
      </div>

      <!-- Tab Switcher -->
      <div class="d-flex justify-content-center gap-2 bg-dark border-bottom border-secondary py-2">
        <button class="btn btn-sm"
                :class="currentTab === 'groups' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'groups'">Tabellen</button>
        <button class="btn btn-sm"
                :class="currentTab === 'top' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'top'">Top-Spieler</button>
        <button class="btn btn-sm"
                :class="currentTab === 'next' ? 'btn-primary' : 'btn-outline-secondary'"
                @click="currentTab = 'next'">Nächste Spiele</button>
      </div>

      <div class="container py-4">

        <!-- Tabellen -->
        <div v-if="currentTab === 'groups'" class="mb-5">
          <h5 class="mb-3 border-bottom border-secondary pb-2">Gruppenphase</h5>
          <div v-if="Object.keys(groupStandings).length" class="row g-3">
            <div v-for="(rows, gname) in groupStandings" :key="gname" class="col-sm-6 col-lg-4">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-header bg-dark border-secondary fw-semibold">{{ gname }}</div>
                <div class="table-responsive">
                  <table class="table table-dark table-sm mb-0">
                    <thead>
                      <tr><th>#</th><th>Team</th><th class="text-center">P</th><th class="text-center">S/N</th><th class="text-center">±</th></tr>
                    </thead>
                    <tbody>
                      <tr v-for="(r, idx) in rows" :key="r.name"
                          :class="idx < 2 ? 'table-success' : ''">
                        <td class="fw-bold">{{ idx + 1 }}</td>
                        <td>{{ r.name }}</td>
                        <td class="text-center fw-bold">{{ r.points }}</td>
                        <td class="text-center text-secondary">{{ r.wins }}/{{ r.losses }}</td>
                        <td class="text-center" :class="r.cupsDiff > 0 ? 'text-success' : r.cupsDiff < 0 ? 'text-danger' : ''">
                          {{ r.cupsDiff > 0 ? '+' : '' }}{{ r.cupsDiff }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-secondary">Keine Gruppenstände vorhanden.</div>

          <div v-if="koRounds.length" class="mt-4">
            <h6 class="text-secondary mb-2">K.O.-Phase</h6>
            <div v-for="round in koRounds" :key="round.round_name" class="mb-3">
              <div class="fw-semibold text-white mb-2">{{ round.round_name }}</div>
              <div class="row g-2">
                <div v-for="(m, idx) in round.matches" :key="idx" class="col-sm-6 col-lg-4">
                  <div class="card bg-dark border-secondary p-3 text-light small h-100">
                    <div class="d-flex align-items-center justify-content-between">
                      <span :class="m.winner === m.team1 ? 'fw-bold text-success' : ''">{{ m.team1 || '?' }}</span>
                      <span class="text-secondary mx-2">vs</span>
                      <span :class="m.winner === m.team2 ? 'fw-bold text-success' : ''">{{ m.team2 || '?' }}</span>
                    </div>
                    <div v-if="m.winner" class="text-center text-success mt-1 small">🏆 {{ m.winner }}</div>
                    <div v-if="m.winner" class="text-center text-secondary mt-0" style="font-size:0.75rem">
                      {{ m.cups_team1 }} : {{ m.cups_team2 }} Becher
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top-Spieler -->
        <div v-else-if="currentTab === 'top'" class="mb-5">
          <h5 class="mb-3 border-bottom border-secondary pb-2">Top-Spieler (Becher)</h5>
          <div v-if="topPlayers.length" class="list-group">
            <div v-for="(p, idx) in topPlayers" :key="p.label"
                 class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center">
              <span><strong>{{ idx + 1 }}.</strong> {{ p.label }}</span>
              <span class="text-success fw-bold">{{ p.cups }} Becher</span>
            </div>
          </div>
          <div v-else class="text-secondary">
            Keine Spieler-Statistiken verfügbar. (Spieler-Becherzahlen werden derzeit nicht erfasst.)
          </div>
        </div>

        <!-- Nächste Spiele -->
        <div v-else-if="currentTab === 'next'" class="mb-5">
          <h5 class="mb-3 border-bottom border-secondary pb-2">Nächste Spiele</h5>
          <div v-if="upcomingMatches.length">
            <div v-for="(m, idx) in upcomingMatches" :key="idx"
                 class="card bg-dark border-secondary p-3 mb-2 d-flex flex-row align-items-center gap-3">
              <span class="badge" :class="phaseBadgeClass">{{ phaseLabel }}</span>
              <span class="badge bg-secondary">{{ m.group_name || m.round || '—' }}</span>
              <span class="fw-semibold">{{ m.team1 }}</span>
              <span class="text-secondary">vs</span>
              <span class="fw-semibold">{{ m.team2 }}</span>
            </div>
          </div>
          <div v-else class="text-secondary">Keine anstehenden Spiele.</div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api.js'
import { useTournamentStore } from '../stores/tournament.js'

const route = useRoute()
const store = useTournamentStore()

const loading = ref(true)
const valid   = ref(false)
const token   = computed(() => route.query.token || route.query.mobile_token || '')

const tournament     = computed(() => store.tournament)
const groupStandings = computed(() => store.groupStandings)
const koRounds       = computed(() => store.koPhase?.rounds ?? [])
const wsConnected    = computed(() => store.wsConnected)
const currentTab     = ref('groups')

const upcomingMatches = computed(() => {
  const matches = store.groupPhase?.matches ?? {}
  const all = Object.values(matches).flat()
  return all.filter(m => !m.winner).slice(0, 5)
})

const topPlayers = computed(() => {
  // Keine Einzelspieler-Stats vorhanden -> Placeholder auf Team-Basis
  const flat = Object.values(groupStandings.value).flat()
  return [...flat]
    .sort((a, b) => b.cupsFor - a.cupsFor)
    .slice(0, 10)
    .map(t => ({
      label: t.name, // Team-Name als Proxy
      cups: t.cupsFor
    }))
})

const phaseLabel = computed(() => {
  const phase = store.tournament?.current_phase ?? 'group'
  if (phase === 'ko') return 'K.O.'
  if (phase === 'playin') return 'Play-In'
  return 'Gruppenphase'
})
const phaseBadgeClass = computed(() => {
  const phase = store.tournament?.current_phase ?? 'group'
  if (phase === 'ko') return 'bg-danger'
  if (phase === 'playin') return 'bg-warning text-dark'
  return 'bg-primary'
})

onMounted(async () => {
  if (!token.value) { loading.value = false; return }
  try {
    const t = route.query.tournament_id
    // Try to find tournament by browsing the state via mobile endpoint
    // We need tournament_id — it comes from the QR URL or we try all
    const tournamentId = route.query.id || route.query.tournament_id
    if (tournamentId) {
      const data = await api.tournaments.mobileState(tournamentId, token.value)
      if (!data.error) {
        store.tournament = data.tournament
        store.teams = data.teams ?? []
        store.groupPhase = data.group_phase ?? {}
        store.groupStandings = data.group_standings ?? {}
        store.playin = data.playin ?? {}
        store.koPhase = data.ko_phase ?? { rounds: [] }
        valid.value = true
        store.connectMobile(tournamentId, token.value)
      }
    } else {
      valid.value = false
    }
  } catch { valid.value = false }
  finally { loading.value = false }
})

onUnmounted(() => {
  store.disconnect()
})
</script>
