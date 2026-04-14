<template>
  <nav class="navbar navbar-dark bg-black border-bottom border-secondary">
    <div class="container d-flex justify-content-between align-items-center">

      <!-- Logo + Titel (klickbar → Titelseite) -->
      <button
        class="navbar-brand d-flex align-items-center gap-2 btn btn-link p-0 m-0 text-decoration-none"
        type="button"
        @click="$emit('go-home')"
      >
        <img
          src="/weiß.png"
          alt="Turnierhalle Logo"
          class="logo-img"
        />
        <div class="d-flex flex-column text-start">
          <span class="fw-bold">Turnierhalle</span>
          <small class="text-secondary">Beer Pong</small>
        </div>
      </button>

      <div class="d-flex align-items-center gap-3">
        <span v-if="hasActive" class="small text-secondary d-none d-md-inline">
          Aktives Turnier:
          <strong class="text-white">{{ tournamentName }}</strong>
          (Phase: {{ tournamentPhase }})
        </span>
        <slot name="extra" />
        <button class="btn btn-outline-secondary btn-sm" @click="$emit('create-new')">
          Neues Turnier
        </button>
        <button class="btn btn-primary btn-sm" @click="$emit('open-loader')">
          Turnier laden
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  hasActive: { type: Boolean, default: false },
  tournamentName: { type: String, default: '' },
  tournamentPhase: { type: String, default: 'group' },
})
defineEmits(['create-new', 'open-loader', 'go-home'])
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
}
.logo-img {
  height: 32px;
  width: auto;
  object-fit: contain;
}
</style>
