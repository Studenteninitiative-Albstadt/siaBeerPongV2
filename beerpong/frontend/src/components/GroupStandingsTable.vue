<template>
  <div class="table-responsive">
    <table class="table table-dark table-hover mb-0 align-middle standings-table" :class="{ 'table-sm': compact }">
      <thead>
        <tr>
          <th class="ps-3 standings-table__rank">#</th>
          <th>Team</th>
          <th class="text-center">St</th>
          <th class="text-center">Pkt</th>
          <th class="text-center">S</th>
          <th class="text-center">N</th>
          <th class="text-center">B+</th>
          <th class="text-center">B-</th>
          <th class="text-center">±</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, idx) in rows"
          :key="row.name + idx"
          :class="statusAt(row, idx).rowClass"
        >
          <td class="ps-3 fw-bold">{{ idx + 1 }}.</td>
          <td class="text-truncate standings-table__team-cell" :style="{ maxWidth: maxNameWidth }" :title="row.name">
            <span
              v-if="isActive(row.name)"
              class="standings-table__live-dot"
              title="Dieses Team spielt gerade live"
            ></span>
            <span>{{ row.name }}</span>
            <span
              v-if="statusAt(row, idx).tagLabel"
              class="badge ms-1"
              :class="statusAt(row, idx).tagClass || 'bg-warning text-dark'"
              :title="statusAt(row, idx).tagTitle || ''"
            >
              {{ statusAt(row, idx).tagLabel }}
            </span>
          </td>
          <td class="text-center">
            <span class="badge rounded-pill" :class="statusAt(row, idx).badgeClass">
              {{ statusAt(row, idx).label }}
            </span>
          </td>
          <td class="text-center fw-bold standings-table__points">{{ row.points }}</td>
          <td class="text-center text-success fw-semibold">{{ row.wins }}</td>
          <td class="text-center text-danger fw-semibold">{{ row.losses }}</td>
          <td class="text-center">{{ row.cupsFor }}</td>
          <td class="text-center">{{ row.cupsAgainst }}</td>
          <td
            class="text-center fw-bold"
            :class="row.cupsDiff > 0 ? 'text-success' : row.cupsDiff < 0 ? 'text-danger' : ''"
          >
            {{ row.cupsDiff > 0 ? '+' : '' }}{{ row.cupsDiff }}
          </td>
        </tr>
        <tr v-if="rows.length === 0">
          <td colspan="9" class="text-center text-light py-4">{{ emptyText }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  rows: { type: Array, default: () => [] },
  activeTeams: { type: Array, default: () => [] },
  emptyText: { type: String, default: 'Noch keine Daten' },
  compact: { type: Boolean, default: false },
  maxNameWidth: { type: String, default: '180px' },
  statusFor: { type: Function, default: null },
})

function isActive(teamName) {
  return (props.activeTeams || []).includes(teamName)
}

function defaultStatusFor(_row, idx) {
  if (idx < 2) {
    return {
      label: 'Direkt',
      badgeClass: 'bg-success',
      rowClass: 'table-success',
      tagLabel: '',
      tagClass: '',
      tagTitle: '',
    }
  }
  return {
    label: '—',
    badgeClass: 'bg-secondary',
    rowClass: '',
    tagLabel: '',
    tagClass: '',
    tagTitle: '',
  }
}

function statusAt(row, idx) {
  return props.statusFor ? (props.statusFor(row, idx) || defaultStatusFor(row, idx)) : defaultStatusFor(row, idx)
}
</script>

<style scoped>
.standings-table__rank {
  width: 44px;
}

.standings-table__team-cell {
  font-size: 1.02rem;
}

.standings-table__points {
  font-size: 1.1rem;
}

.standings-table__live-dot {
  display: inline-block;
  width: 0.62rem;
  height: 0.62rem;
  border-radius: 999px;
  margin-right: 0.45rem;
  background: #ff3b30;
  box-shadow: 0 0 0 rgba(255, 59, 48, 0.7);
  animation: standings-live-pulse 1.4s ease-in-out infinite;
  vertical-align: middle;
}

.table-sm .standings-table__team-cell {
  font-size: 0.9rem;
}

.table-sm .standings-table__points {
  font-size: 0.98rem;
}

@keyframes standings-live-pulse {
  0% {
    transform: scale(0.92);
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.68);
  }
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 0.42rem rgba(255, 59, 48, 0);
  }
  100% {
    transform: scale(0.92);
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0);
  }
}
</style>
