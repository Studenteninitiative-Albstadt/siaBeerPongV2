<template>
  <section class="mb-5">
    <!-- Titel mittig -->
    <div class="text-center mb-4">
      <h1 class="display-5 fw-bold mb-2">
        Willkommen zum SIA Bier Pong Turnier
      </h1>
      <p class="lead text-secondary mb-0">
        Sommersemester 2026
      </p>
    </div>

    <div class="row g-4">
      <!-- Links: TL;DR -->
      <div class="col-md-6">
        <div class="card bg-elevated border-secondary h-100 text-light">
          <div class="card-header bg-elevated border-secondary">
            <strong>TL;DR</strong>
          </div>
          <div class="card-body">
            <ul class="mb-0">
              <li>Gespielt wird in Gruppenphase → KO-System.</li>
              <li>
                Pro Spiel:
                <strong>2 × 0,33&nbsp;l Bier</strong>
                <span class="text-secondary"> (an der Bar für 2,50&nbsp;€).</span>
              </li>
              <li>Je nach Teilnehmeranzahl kann es ein Play-In für die KO-Phase geben.</li>
              <li>Gewertet werden Siege/Niederlagen und getroffene/kassierte Becher.</li>
              <li>Der Sieger des Turniers gewinnt einen <strong>Bierkasten</strong>.</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Rechts: Upcoming Events -->
      <div class="col-md-6">
        <div class="card bg-elevated border-secondary h-100 text-light">
          <div class="card-header bg-elevated border-secondary d-flex justify-content-between align-items-center">
            <strong>Upcoming Events</strong>
          </div>
          <div class="card-body">
            <ul class="list-unstyled mb-0">
              <li class="mb-3">
                <div class="fw-semibold">Just Open</div>
                <small class="text-secondary">
                  18.11.2025 · 20:00 · Plan B
                </small>
              </li>
              <li class="mb-3">
                <div class="fw-semibold">Blacklight</div>
                <small class="text-secondary">
                  20.11.2025 · 20:00 · Plan B
                </small>
              </li>
              <li>
                <div class="fw-semibold">Mental Health Coffee Break</div>
                <small class="text-secondary">
                  21.11.2025 · 14:00 · Plan B
                </small>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
</script>

<style scoped>
.card.bg-elevated {
  background: #15171c;
  color: #f8f9fa; /* Basis-Schriftfarbe hell */
}

.card.bg-elevated:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  transition: box-shadow 0.2s ease;
}
</style>
