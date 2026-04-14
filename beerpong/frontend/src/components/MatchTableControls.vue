<template>
  <div class="match-table-controls bg-dark p-3 rounded border border-secondary text-light">
    <h5 class="text-center mb-4">Live Tisch-Verwaltung</h5>
    
    <div class="d-flex justify-content-between align-items-center">
      <!-- Team 1 (Links) -->
      <div class="team-side flex-fill text-center">
        <h6 class="text-white">{{ team1Name }}</h6>
        <div class="text-secondary small mb-2" v-if="team1Players">{{ team1Players }}</div>
        <div class="cup-grid">
          <div v-for="(row, rIdx) in team1Rows" :key="'t1-row-'+rIdx" class="cup-row">
            <div 
              v-for="cup in row" 
              :key="'t1-cup-'+cup.idx"
              class="cup"
              :class="{ 'cup-standing': cup.val, 'cup-hit': !cup.val, 'cup-rerack-mode': rerackMode === 'team1' }"
              @click="handleCupHit('team1', cup.idx)"
              :title="rerackMode === 'team1' ? 'Becher umschalten' : 'Becher treffen'"
            ></div>
          </div>
        </div>
        <div v-if="rerackMode === 'team1'" class="mt-3">
          <button class="btn btn-sm btn-success me-2" @click="saveRerack">Speichern</button>
          <button class="btn btn-sm btn-outline-danger" @click="cancelRerack">Abbruch</button>
        </div>
        <div v-else class="mt-3">
          <button class="btn btn-sm btn-outline-warning me-2" @click="undo('team1')" :disabled="rerackMode === 'team2'">
            ↶ Undo
          </button>
          <button class="btn btn-sm btn-outline-info" @click="startRerack('team1')" :disabled="team1RerackUsed || rerackMode === 'team2'">
            Re-Rack
          </button>
        </div>
      </div>

      <!-- Tisch-Netz / Mitte -->
      <div class="table-net mx-3 d-flex flex-column justify-content-center align-items-center">
        <div class="net-line"></div>
        <span class="text-secondary fw-bold my-2">VS</span>
        <div class="net-line"></div>
      </div>

      <!-- Team 2 (Rechts) -->
      <div class="team-side flex-fill text-center">
        <h6 class="text-white">{{ team2Name }}</h6>
        <div class="text-secondary small mb-2" v-if="team2Players">{{ team2Players }}</div>
        <div class="cup-grid reverse-grid">
          <div v-for="(row, rIdx) in team2Rows" :key="'t2-row-'+rIdx" class="cup-row">
            <div 
              v-for="cup in row" 
              :key="'t2-cup-'+cup.idx"
              class="cup"
              :class="{ 'cup-standing': cup.val, 'cup-hit': !cup.val, 'cup-rerack-mode': rerackMode === 'team2' }"
              @click="handleCupHit('team2', cup.idx)"
              :title="rerackMode === 'team2' ? 'Becher umschalten' : 'Becher treffen'"
            ></div>
          </div>
        </div>
        <div v-if="rerackMode === 'team2'" class="mt-3">
          <button class="btn btn-sm btn-success me-2" @click="saveRerack">Speichern</button>
          <button class="btn btn-sm btn-outline-danger" @click="cancelRerack">Abbruch</button>
        </div>
        <div v-else class="mt-3">
          <button class="btn btn-sm btn-outline-warning me-2" @click="undo('team2')" :disabled="rerackMode === 'team1'">
            ↶ Undo
          </button>
          <button class="btn btn-sm btn-outline-info" @click="startRerack('team2')" :disabled="team2RerackUsed || rerackMode === 'team1'">
            Re-Rack
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  tournamentId: Number,
  matchId: String,
  team1Name: String,
  team2Name: String,
  team1Players: String,
  team2Players: String,
  is10Cups: Boolean,
  cupsStateTeam1: Array,
  cupsStateTeam2: Array,
  team1RerackUsed: Boolean,
  team2RerackUsed: Boolean
})

const emit = defineEmits(['cup-hit', 'undo', 'rerack'])

const rerackMode = ref(null) // 'team1', 'team2' oder null
const localCups = ref([])

function startRerack(teamKey) {
  rerackMode.value = teamKey
  localCups.value = teamKey === 'team1' ? [...props.cupsStateTeam1] : [...props.cupsStateTeam2]
}
function cancelRerack() {
  rerackMode.value = null
}
function saveRerack() {
  emit('rerack', { matchId: props.matchId, teamKey: rerackMode.value, newState: [...localCups.value] })
  rerackMode.value = null
}

function buildPyramid(cupsArray, is10Cups) {
  if (!cupsArray || cupsArray.length === 0) return []
  
  if (is10Cups) {
    return [
      [ {idx:0, val:cupsArray[0]}, {idx:1, val:cupsArray[1]}, {idx:2, val:cupsArray[2]}, {idx:3, val:cupsArray[3]} ],
      [ {idx:4, val:cupsArray[4]}, {idx:5, val:cupsArray[5]}, {idx:6, val:cupsArray[6]} ],
      [ {idx:7, val:cupsArray[7]}, {idx:8, val:cupsArray[8]} ],
      [ {idx:9, val:cupsArray[9]} ]
    ]
  } else {
    // Standard 6 Becher (Short Game)
    return [
      [ {idx:0, val:cupsArray[0]}, {idx:1, val:cupsArray[1]}, {idx:2, val:cupsArray[2]} ],
      [ {idx:3, val:cupsArray[3]}, {idx:4, val:cupsArray[4]} ],
      [ {idx:5, val:cupsArray[5]} ]
    ]
  }
}

const team1Rows = computed(() => {
  const arr = rerackMode.value === 'team1' ? localCups.value : props.cupsStateTeam1
  return buildPyramid(arr, props.is10Cups)
})
const team2Rows = computed(() => {
  const arr = rerackMode.value === 'team2' ? localCups.value : props.cupsStateTeam2
  return buildPyramid(arr, props.is10Cups)
})

function handleCupHit(teamKey, cupIndex) {
  if (rerackMode.value) {
    if (rerackMode.value === teamKey) {
      localCups.value[cupIndex] = !localCups.value[cupIndex]
    }
    return
  }
  const isStanding = teamKey === 'team1' ? props.cupsStateTeam1[cupIndex] : props.cupsStateTeam2[cupIndex]
  if (isStanding) {
    emit('cup-hit', { matchId: props.matchId, teamKey, cupIndex })
  }
}

function undo(teamKey) {
  emit('undo', { matchId: props.matchId, teamKey })
}
</script>

<style scoped>
.cup-grid {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 15px;
}
.reverse-grid {
  flex-direction: row-reverse; /* Dreht die Pyramide für das gegnerische Team */
}
.cup-row {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}
.cup {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #d32f2f; /* Roter Partybecher */
  border: 3px solid rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  box-shadow: inset 0 -4px 8px rgba(0,0,0,0.3), 0 4px 6px rgba(0,0,0,0.2);
}
.cup-hit {
  opacity: 0.15;
  transform: scale(0.75);
  pointer-events: none; /* Getroffene Becher können nicht nochmal angeklickt werden */
}
.cup-rerack-mode {
  pointer-events: auto !important; /* Erlaube das Anklicken auch von getroffenen Bechern */
  cursor: pointer;
}
.cup-rerack-mode.cup-hit {
  border-style: dashed;
  opacity: 0.4;
}
.table-net {
  height: 150px;
}
.net-line {
  width: 2px;
  flex-grow: 1;
  background: repeating-linear-gradient(to bottom, #6c757d, #6c757d 10px, transparent 10px, transparent 20px);
}
</style>