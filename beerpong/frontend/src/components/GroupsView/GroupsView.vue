<template>
  <section class="mx-auto" style="max-width: 1400px;">
    <!-- Kopf -->
    <div class="d-flex justify-content-between align-items-center mb-2">
      <h2 class="mb-0">Gruppenphase</h2>
      <div class="d-flex align-items-center gap-3">
        <small v-if="saveState === 'saving'" class="text-info">Speichere…</small>
        <small v-else-if="saveState === 'saved'" class="text-success">Gespeichert</small>
        <small v-else-if="saveState === 'error'" class="text-danger">Speichern fehlgeschlagen</small>
        <button class="btn btn-outline-light" @click="$emit('back')">Zur Startseite</button>
        <button class="btn btn-outline-light" @click="reloadAll" :disabled="loading">Daten laden</button>
        <button class="btn btn-primary" :disabled="!canProceedKo" @click="goNext">
          Weiter KO-Phase
        </button>
      </div>
    </div>

    <!-- Ansichts-Umschalter -->
    <div class="btn-group mb-4 w-100 shadow-sm" v-if="renderGroups.length > 0">
      <input type="radio" class="btn-check" id="btnradio1" value="tables" v-model="viewMode">
      <label class="btn btn-outline-info" for="btnradio1">🏓 Live-Tische (Automatisch)</label>

      <input type="radio" class="btn-check" id="btnradio2" value="groups" v-model="viewMode">
      <label class="btn btn-outline-info" for="btnradio2">📊 Gruppen & Tabellen</label>
    </div>

    <!-- Turnier-Info -->
    <div class="card bg-dark border-secondary mb-4 text-light" v-show="viewMode === 'groups'">
      <div class="card-body py-3">
        <div class="row">
          <div class="col-md-4">
            <strong>Teilnehmer:</strong>
            {{ (tournament?.participantCount ?? tournament?.participant_count) ?? teams.length }} Teams
          </div>
          <div class="col-md-4"><strong>Becher pro Spiel:</strong> {{ cupsTarget }}</div>
          <div class="col-md-4"><strong>Gruppen (Vorschau):</strong> {{ autoGroupsPreview.length || '–' }}</div>
        </div>
        <div class="mt-2">
          <!-- Buttons entfernt, da jetzt automatisch beim Erstellen -->
        </div>
      </div>
    </div>

    <details class="card bg-dark border-secondary mb-4 text-light">
      <summary class="card-header bg-dark border-secondary" style="cursor:pointer;">
        Team-Spieler bearbeiten
      </summary>
      <div class="card-body">
        <div class="small text-secondary mb-3">
          Diese Zuordnung wird nur auf den Teams gespeichert. Gruppenspiele und Ergebnisse bleiben unverändert.
        </div>
        <div class="row g-3">
          <div v-for="teamName in teams" :key="`team-player-${teamName}`" class="col-lg-6">
            <div v-if="teamPlayerDrafts[teamName]" class="border border-secondary rounded p-3 h-100">
              <div class="fw-bold text-white mb-3">{{ teamName }}</div>
              <div class="row g-2">
                <div class="col-6">
                  <label class="form-label small text-secondary">Spieler 1</label>
                  <input
                    v-model="teamPlayerDrafts[teamName].player1"
                    type="text"
                    class="form-control bg-dark text-light border-secondary"
                  >
                </div>
                <div class="col-6">
                  <label class="form-label small text-secondary">Spieler 2</label>
                  <input
                    v-model="teamPlayerDrafts[teamName].player2"
                    type="text"
                    class="form-control bg-dark text-light border-secondary"
                  >
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="d-flex align-items-center gap-3 mt-3">
          <button class="btn btn-outline-light" @click="syncTeamPlayerDrafts">Zurücksetzen</button>
          <button class="btn btn-primary" :disabled="teamPlayerSaveState === 'saving'" @click="saveTeamPlayersOnly">
            Spieler speichern
          </button>
          <small v-if="teamPlayerSaveState === 'saving'" class="text-info">Speichere…</small>
          <small v-else-if="teamPlayerSaveState === 'saved'" class="text-success">Spieler gespeichert</small>
          <small v-else-if="teamPlayerSaveState === 'error'" class="text-danger">Speichern fehlgeschlagen</small>
        </div>
      </div>
    </details>

    <!-- Ladehinweise -->
    <div v-if="loading" class="alert alert-dark border-secondary my-3">Lade…</div>
    <div v-else-if="renderGroups.length === 0" class="alert alert-dark border-secondary my-3">
      Noch keine Gruppendaten verfügbar. Bitte prüfe die Turnier-Einstellungen.
    </div>

    <!-- ================= LIVE TISCHE ANSICHT ================= -->
    <div v-if="viewMode === 'tables' && renderGroups.length > 0">

      <!-- Tisch-Verwaltung -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0 text-light">Aktive Tische ({{ activeTableCount }})</h5>
        <div class="btn-group">
          <button class="btn btn-sm btn-outline-secondary" @click="activeTableCount = Math.max(1, activeTableCount - 1)">- Tisch entfernen</button>
          <button class="btn btn-sm btn-outline-secondary" @click="activeTableCount++">+ Tisch hinzufügen</button>
        </div>
      </div>

      <!-- Aktive Tische -->
      <div class="row g-4 mb-5">
        <div v-for="(m, i) in activeMatches" :key="m.id" class="col-12 col-xl-6">
          <div class="d-flex justify-content-between align-items-end mb-2 px-2">
            <h4 class="text-warning mb-0 fw-bold">Tisch {{ m.table_no || i + 1 }}</h4>
            <span class="badge bg-secondary">{{ m.group_name }}</span>
          </div>

          <!-- Schützenauswahl Overlay für diesen Tisch -->
          <div v-if="pendingShooter && pendingShooter.matchId == m.id" class="p-5 border border-warning rounded bg-dark text-center shadow-lg" style="min-height: 300px;">
            <h4 class="text-warning mb-4">
              {{ pendingShooter.mode === 'overtime_credit' ? `Nachwurf für ${pendingShooter.teamName}!` : `Treffer für ${pendingShooter.teamName}!` }}
            </h4>
            <template v-if="pendingShooter.mode === 'overtime_credit'">
              <p class="text-light mb-2">
                Verteile die {{ pendingShooter.bonusCupCount }} Nachwurf-Becher auf die Spieler.
              </p>
              <div class="text-secondary small mb-4">
                Noch zu verteilen: {{ getGroupOvertimeRemainingCups() }}
              </div>
              <div class="d-flex justify-content-center gap-3 flex-wrap mb-4">
                <div v-if="pendingShooter.p1" class="group-credit-card">
                  <div class="text-light fw-semibold mb-2">{{ pendingShooter.p1 }}</div>
                  <div class="btn-group" role="group" aria-label="Nachwurf Gruppe Spieler 1">
                    <button class="btn btn-outline-secondary" @click="adjustGroupOvertimeAllocation('p1', -1)" :disabled="(pendingShooter.bonusP1 || 0) <= 0">−</button>
                    <span class="btn btn-outline-light disabled group-credit-count">{{ pendingShooter.bonusP1 || 0 }}</span>
                    <button class="btn btn-outline-warning" @click="adjustGroupOvertimeAllocation('p1', 1)" :disabled="getGroupOvertimeRemainingCups() <= 0">+</button>
                  </div>
                </div>
                <div v-if="pendingShooter.p2" class="group-credit-card">
                  <div class="text-light fw-semibold mb-2">{{ pendingShooter.p2 }}</div>
                  <div class="btn-group" role="group" aria-label="Nachwurf Gruppe Spieler 2">
                    <button class="btn btn-outline-secondary" @click="adjustGroupOvertimeAllocation('p2', -1)" :disabled="(pendingShooter.bonusP2 || 0) <= 0">−</button>
                    <span class="btn btn-outline-light disabled group-credit-count">{{ pendingShooter.bonusP2 || 0 }}</span>
                    <button class="btn btn-outline-warning" @click="adjustGroupOvertimeAllocation('p2', 1)" :disabled="getGroupOvertimeRemainingCups() <= 0">+</button>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <p class="text-light mb-4">Wer hat den Becher getroffen?</p>
              <div class="d-flex justify-content-center gap-3 mb-4">
                <button
                  v-if="pendingShooter.p1"
                  class="btn btn-lg px-4 py-3 fw-bold"
                  :class="selectedPlayer === pendingShooter.p1 ? 'btn-success scale-up' : 'btn-outline-success'"
                  @click="selectShooter(pendingShooter.p1)"
                >
                  {{ pendingShooter.p1 }}
                </button>
                <button
                  v-if="pendingShooter.p2"
                  class="btn btn-lg px-4 py-3 fw-bold"
                  :class="selectedPlayer === pendingShooter.p2 ? 'btn-success scale-up' : 'btn-outline-success'"
                  @click="selectShooter(pendingShooter.p2)"
                >
                  {{ pendingShooter.p2 }}
                </button>
              </div>
            </template>

            <div class="d-flex justify-content-center gap-2">
              <button class="btn btn-outline-secondary" @click="cancelShooter">
                {{ pendingShooter.mode === 'overtime_credit' ? 'Zurück' : 'Abbruch (Undo)' }}
              </button>
              <button
                class="btn btn-primary btn-lg px-5 fw-bold"
                :disabled="pendingShooter.mode === 'overtime_credit' ? !isGroupOvertimeAllocationComplete() : !selectedPlayer"
                @click="confirmShooter"
              >
                {{ pendingShooter.mode === 'overtime_credit' ? 'Nachwurf Bestätigen' : 'Treffer Bestätigen' }}
              </button>
            </div>
          </div>

          <!-- Abschluss-Dialog Overlay -->
          <div v-else-if="pendingConclusion && pendingConclusion.match.id === m.id" class="p-5 border border-primary rounded bg-dark text-center shadow-lg" style="min-height: 300px;">
            <h4 class="text-primary mb-4">Spielabschluss</h4>

            <!-- Step 1: Nachwurf? -->
            <template v-if="pendingConclusion.step === 'NACHWURF'">
              <p class="text-light mb-4 fs-5">Alle Becher getroffen! Gibt es einen <strong>Nachwurf</strong>?</p>
              <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-lg btn-primary px-4 fw-bold" @click="conclusionStep('ALL_HIT')">Ja (Nachwurf)</button>
                <button class="btn btn-lg btn-outline-primary px-4 fw-bold" @click="conclusionStep('END_QUERY')">Nein (Direkter Sieg)</button>
              </div>
            </template>

            <!-- Step 2: Alle getroffen? -->
            <template v-else-if="pendingConclusion.step === 'ALL_HIT'">
              <p class="text-light mb-4 fs-5">Wurden beim Nachwurf <strong>alle verbleibenden Becher</strong> getroffen?</p>
              <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-lg btn-warning px-4 fw-bold" @click="conclusionOvertime()">Ja (Verlängerung 3 Becher)</button>
                <button class="btn btn-lg btn-outline-primary px-4 fw-bold" @click="conclusionStep('END_QUERY')">Nein (Sieg nach Nachwurf)</button>
              </div>
            </template>

            <!-- Step 3: Spiel beenden? -->
            <template v-else-if="pendingConclusion.step === 'END_QUERY'">
              <p class="text-light mb-4 fs-5">Soll das Spiel jetzt <strong>final beendet</strong> werden?</p>
              <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-lg btn-success px-4 fw-bold" @click="finishConclusion(true)">Ja (Spiel abschließen)</button>
                <button class="btn btn-lg btn-outline-danger px-4 fw-bold" @click="finishConclusion(false)">Nein (Zurück zum Spielstand)</button>
              </div>
            </template>

            <button v-if="pendingConclusion.step !== 'NACHWURF'" class="btn btn-sm btn-outline-secondary mt-5" @click="conclusionBack">← Zurück</button>
            <button v-else class="btn btn-sm btn-outline-secondary mt-5" @click="pendingConclusion = null">Abbrechen</button>
          </div>

          <!-- Tisch Ansicht -->
          <MatchTableControls
            v-else
            :tournament-id="tournamentId"
            :match-id="String(m.id)"
            :team1-name="m.team1"
            :team2-name="m.team2"
            :team1-players="formatPlayers(m.team1)"
            :team2-players="formatPlayers(m.team2)"
            :is10-cups="cupsTarget === 10"
            :cups-state-team1="m.cups_state_team1 || Array(cupsTarget).fill(true)"
            :cups-state-team2="m.cups_state_team2 || Array(cupsTarget).fill(true)"
            :team1-rerack-used="m.team1_rerack_used"
            :team2-rerack-used="m.team2_rerack_used"
            @cup-hit="onLiveCupHit(m.group_name, m.originalIndex, $event)"
            @undo="onLiveUndo(m.group_name, m.originalIndex, $event)"
            @rerack="onLiveRerack(m.group_name, m.originalIndex, $event)"
            @forfeit="onLiveForfeit(m.group_name, m.originalIndex, $event)"
          />
        </div>
        <div v-if="activeMatches.length === 0" class="col-12">
          <div class="alert alert-success text-center py-5">
            <h4 class="mb-0">🎉 Alle Gruppenspiele sind abgeschlossen!</h4>
          </div>
        </div>
      </div>

      <!-- Warteschlange -->
      <div v-if="queueMatches.length > 0" class="card bg-dark border-secondary group-queue-card">
        <div class="card-header bg-secondary text-light fw-bold d-flex justify-content-between align-items-start gap-3">
          <div>
            <div>Als Nächstes (Warteschlange)</div>
            <div class="small text-light-emphasis fw-normal mt-1">
              Wartende Spiele sind per Drag & Drop, Buttons oder Fairness-Optimierung umsortierbar.
            </div>
          </div>
          <div class="d-flex flex-wrap align-items-center justify-content-end gap-2">
            <button
              class="btn btn-sm btn-outline-light"
              @click="optimizeQueueFairness"
              :disabled="queueMatches.length < 2"
            >
              Fair sortieren
            </button>
            <span class="badge bg-dark border border-light-subtle flex-shrink-0">{{ upcomingMatchesTotal }} ausstehend</span>
          </div>
        </div>
        <div
          class="list-group list-group-flush group-queue-list"
          @dragover.prevent="onQueueListDragOver"
          @drop.prevent="onQueueListDrop"
        >
          <div
            v-for="(m, idx) in queueMatches"
            :key="matchKey(m)"
            class="list-group-item bg-dark text-light border-secondary group-queue-item"
            :class="{
              'group-queue-item--dragging': draggedQueueMatchKey === matchKey(m),
              'group-queue-item--drop-before': hoveredQueueMatchKey === matchKey(m) && hoveredQueuePosition === 'before',
              'group-queue-item--drop-after': hoveredQueueMatchKey === matchKey(m) && hoveredQueuePosition === 'after',
            }"
            draggable="true"
            @dragstart="onQueueDragStart(m, $event)"
            @dragend="onQueueDragEnd"
            @dragover.prevent="onQueueDragOver(m, $event)"
            @drop.prevent="onQueueDrop(m, $event)"
          >
            <div class="d-flex align-items-center gap-3 w-100">
              <div class="group-queue-handle" aria-hidden="true">⋮⋮</div>
              <div class="flex-grow-1 group-queue-main">
                <div class="fw-semibold text-truncate">
                  {{ m.team1 }} <strong class="text-secondary mx-2">vs</strong> {{ m.team2 }}
                </div>
                <div class="small text-secondary">#{{ idx + 1 }} in der Warteschlange</div>
              </div>
              <div class="d-flex align-items-center gap-1 flex-shrink-0">
                <button
                  class="btn btn-sm btn-outline-light"
                  @click.stop="moveQueueMatch(m, -1)"
                  :disabled="idx === 0"
                  title="Ein Platz nach oben"
                >
                  ↑
                </button>
                <button
                  class="btn btn-sm btn-outline-light"
                  @click.stop="moveQueueMatch(m, 1)"
                  :disabled="idx === queueMatches.length - 1"
                  title="Ein Platz nach unten"
                >
                  ↓
                </button>
              </div>
              <span class="badge bg-dark border border-secondary flex-shrink-0">{{ m.group_name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Kartenraster -->
    <div v-show="viewMode === 'groups'" class="row g-4">
      <div v-for="group in renderGroups" :key="group.name" class="col-xl-4 col-lg-6">
        <div class="card bg-dark text-light border-secondary h-100 d-flex flex-column">
          <!-- Header -->
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">{{ group.name }}</span>
            <button
              class="btn btn-sm btn-outline-light"
              @click="ensureGroupMatches(group)"
              :disabled="(groupMatches[group.name] || []).length > 0 || group.teams.length < 2"
            >
              Gruppenspiele
            </button>
          </div>

          <!-- Tabelle -->
          <div class="card-body p-0">
            <GroupStandingsTable
              :rows="getFinalStandings(group.name)"
              :active-teams="activeTeamNames"
              :status-for="(_row, idx) => standingStatus(group.name, idx)"
              max-name-width="180px"
              empty-text="Noch keine Daten"
            />

            <!-- Last Cup Shoot-Off Panel -->
            <div v-if="perGroupTiebreak[group.name] || lastCupElimState[group.name]" class="p-3 border-top border-warning">

              <div class="fw-bold text-warning mb-2">⚡ Last Cup Shoot-Off</div>

              <!-- Nicht gestartet -->
              <template v-if="!lastCupElimState[group.name]">
                <div class="text-secondary small mb-2">
                  <span v-if="perGroupTiebreak[group.name]?.fixedFirst">
                    <strong class="text-light">{{ perGroupTiebreak[group.name].fixedFirst }}</strong> ist gesetzt (Platz 1).
                    Plätze 2–{{ perGroupTiebreak[group.name].teams.length + 1 }} gleichauf →
                  </span>
                  <span v-else>3 Teams exakt gleichauf →</span>
                  1 Becher, alle werfen abwechselnd. Wer alleine nicht trifft, scheidet aus.
                </div>
                <button class="btn btn-sm btn-warning" @click="startLastCupElim(group.name)">
                  Shoot-Off starten
                </button>
              </template>

              <!-- Aktive Runde -->
              <template v-else-if="!lastCupElimState[group.name].done">
                <div class="text-secondary small mb-3">
                  Runde <strong class="text-white">{{ lastCupElimState[group.name].roundCount }}</strong>
                  — Hat jedes Team den Becher getroffen?
                </div>

                <!-- Bereits platzierte Teams -->
                <div v-if="lastCupElimState[group.name].topPlaced.length || lastCupElimState[group.name].bottomPlaced.length" class="mb-2 d-flex flex-wrap gap-1">
                  <span v-for="t in lastCupElimState[group.name].topPlaced" :key="'top'+t" class="badge bg-success">✓ {{ t }}</span>
                  <span v-for="t in lastCupElimState[group.name].bottomPlaced" :key="'bot'+t" class="badge bg-danger">✗ {{ t }}</span>
                </div>

                <!-- Noch aktive Teams -->
                <div v-for="team in lastCupElimState[group.name].remaining" :key="team" class="d-flex align-items-center gap-2 mb-2">
                  <span class="flex-fill fw-bold text-white small">{{ team }}</span>
                  <button class="btn btn-sm"
                          :class="lastCupElimState[group.name].currentRound[team] === 'hit' ? 'btn-success' : 'btn-outline-success'"
                          @click="setElimResult(group.name, team, 'hit')">✓ Treffer</button>
                  <button class="btn btn-sm"
                          :class="lastCupElimState[group.name].currentRound[team] === 'miss' ? 'btn-danger' : 'btn-outline-danger'"
                          @click="setElimResult(group.name, team, 'miss')">✗ Fehler</button>
                </div>

                <div class="d-flex gap-2 mt-3">
                  <button class="btn btn-sm btn-primary"
                          :disabled="!isElimRoundComplete(group.name)"
                          @click="evaluateElimRound(group.name)">
                    Runde auswerten
                  </button>
                  <button class="btn btn-sm btn-outline-secondary" @click="resetElim(group.name)">Neu starten</button>
                </div>
              </template>

              <!-- Fertig -->
              <template v-else>
                <div class="text-success small fw-bold mb-2">✅ Shoot-Off abgeschlossen!</div>
                <div v-for="(t, i) in lastCupElimState[group.name].finalRanking" :key="t"
                     class="d-flex align-items-center gap-2 mb-1 small">
                  <span class="badge"
                        :class="i === 0 ? 'bg-success' : i === lastCupElimState[group.name].finalRanking.length - 1 ? 'bg-danger' : 'bg-secondary'">
                    Platz {{ i + 1 + (lastCupElimState[group.name].fixedFirst ? 1 : 0) }}
                  </span>
                  <span class="text-white">{{ t }}</span>
                </div>
                <button class="btn btn-sm btn-outline-secondary mt-2" @click="resetElim(group.name)">Wiederholen</button>
              </template>

            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- Play-In/KO-Block -->
    <div class="card bg-dark border-secondary my-4" v-if="renderGroups.length">
      <div class="card-header bg-dark border-secondary">
        <strong>Play-In / KO-Vorbereitung</strong>
      </div>
      <div class="card-body">
        <div v-if="playInResult" class="mb-3">
          <div class="mb-2">
            <span class="badge bg-secondary">Ergebnis</span>
          </div>
          <div class="row g-3">
            <div class="col-md-4">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-body">
                  <div class="fw-bold text-white mb-2">Direkt qualifiziert</div>
                  <div class="d-flex flex-wrap gap-1">
                    <span
                      v-for="t in playInResult.direct_qualified"
                      :key="t"
                      class="badge bg-success"
                    >
                      {{ t }}
                    </span>
                    <span
                      v-if="playInResult.direct_qualified?.length === 0"
                      class="text-light"
                    >
                      –
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Play-In Matches ODER Rage-Cage-Gruppen -->
            <div class="col-md-8">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-body">
                  <div class="fw-bold text-white mb-2">Play-In</div>

                  <template v-if="(playInResult.playin_matches?.length || 0) > 0">
                    <div
                      v-for="(m, idx) in playInResult.playin_matches"
                      :key="m.match_id || idx"
                      class="d-flex align-items-center gap-2 mb-2"
                    >
                      <span class="badge bg-secondary flex-grow-1 text-start">{{ m.team1 }}</span>
                      <span class="text-light">vs</span>
                      <span class="badge bg-secondary flex-grow-1 text-start">{{ m.team2 }}</span>
                      <span
                        class="badge bg-dark border border-secondary"
                        :title="m.cups_per_game ? `Becher pro Spiel: ${m.cups_per_game}` : 'Standard'"
                      >
                        {{ m.cups_per_game || cupsTarget }} B.
                      </span>
                    </div>
                  </template>

                  <template v-else-if="playInResult.last_cup_shootoff">
                    <div class="alert alert-dark border-warning mb-0">
                      <div class="text-warning fw-bold mb-2">Last Cup Shoot-Off</div>
                      <div class="d-flex flex-wrap gap-1">
                        <span
                          v-for="t in playInResult.last_cup_shootoff.teams"
                          :key="t"
                          class="badge bg-secondary"
                        >
                          {{ t }}
                        </span>
                      </div>
                      <div class="small text-light mt-2">{{ playInResult.last_cup_shootoff.note }}</div>
                    </div>
                  </template>

                  <template v-else-if="(playInResult.rage_cage_groups?.length || 0) > 0">
                    <div
                      v-for="(rc, i) in playInResult.rage_cage_groups"
                      :key="'rc' + i"
                      class="alert alert-dark border-warning"
                    >
                      <div class="text-warning fw-bold mb-2">Rage-Cage</div>
                      <div class="d-flex flex-wrap gap-1">
                        <span v-for="t in rc.teams" :key="t" class="badge bg-secondary">
                          {{ t }}
                        </span>
                      </div>
                      <div class="small text-light mt-2">{{ rc.note }}</div>
                    </div>
                  </template>

                  <div v-else class="text-light">
                    <span v-if="(playInResult.auto_advanced?.length || 0) > 0">
                      Automatisch weiter:
                      <span
                        class="badge bg-success ms-1"
                        v-for="t in playInResult.auto_advanced"
                        :key="t"
                      >
                        {{ t }}
                      </span>
                    </span>
                    <span v-else>Kein Play-In notwendig.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tiebreak-Pläne (gruppenlokal, noch nicht aufgelöst) -->
          <div
            v-if="(playInResult.tiebreaks?.length || 0) > 0"
            class="card bg-dark border-warning mt-3"
          >
            <div class="card-header bg-dark border-warning text-warning">
              <strong>⚡ Offene Shoot-Offs</strong>
            </div>
            <div class="card-body">
              <div v-for="(tb, i) in playInResult.tiebreaks" :key="i" class="mb-2">
                <div class="fw-semibold text-white">{{ tb.group }}</div>
                <div class="text-secondary small">
                  Teams gleichauf: {{ tb.teams.join(', ') }}
                  <span v-if="tb.fixedFirst"> ({{ tb.fixedFirst }} ist Platz 1)</span>
                  → Shoot-Off in der Gruppen-Ansicht starten.
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="playInResult.last_cup_shootoff || playInShootOffState"
            class="card bg-dark border-warning mt-3"
          >
            <div class="card-header bg-dark border-warning text-warning">
              <strong>⚡ Play-In Shoot-Off</strong>
            </div>
            <div class="card-body">
              <template v-if="activePlayInShootOffPlan && !playInShootOffState">
                <div class="text-secondary small mb-2">{{ activePlayInShootOffPlan.note }}</div>
                <button class="btn btn-sm btn-warning" @click="startPlayInShootOff">
                  Shoot-Off starten
                </button>
              </template>

              <template v-else-if="playInShootOffState && !playInShootOffState.done">
                <div class="text-secondary small mb-3">
                  Runde <strong class="text-white">{{ playInShootOffState.roundCount }}</strong>
                  — Wer trifft den letzten Becher?
                </div>

                <div
                  v-if="playInShootOffState.topPlaced.length || playInShootOffState.bottomPlaced.length"
                  class="mb-2 d-flex flex-wrap gap-1"
                >
                  <span
                    v-for="t in playInShootOffState.topPlaced"
                    :key="'playin-top-' + t"
                    class="badge bg-success"
                  >
                    ✓ {{ t }}
                  </span>
                  <span
                    v-for="t in playInShootOffState.bottomPlaced"
                    :key="'playin-bottom-' + t"
                    class="badge bg-danger"
                  >
                    ✗ {{ t }}
                  </span>
                </div>

                <div
                  v-for="team in playInShootOffState.remaining"
                  :key="'playin-round-' + team"
                  class="d-flex align-items-center gap-2 mb-2"
                >
                  <span class="flex-fill fw-bold text-white small">{{ team }}</span>
                  <button
                    class="btn btn-sm"
                    :class="playInShootOffState.currentRound[team] === 'hit' ? 'btn-success' : 'btn-outline-success'"
                    @click="setPlayInShootOffResult(team, 'hit')"
                  >
                    ✓ Treffer
                  </button>
                  <button
                    class="btn btn-sm"
                    :class="playInShootOffState.currentRound[team] === 'miss' ? 'btn-danger' : 'btn-outline-danger'"
                    @click="setPlayInShootOffResult(team, 'miss')"
                  >
                    ✗ Fehler
                  </button>
                </div>

                <div class="d-flex gap-2 mt-3">
                  <button
                    class="btn btn-sm btn-primary"
                    :disabled="!isPlayInShootOffRoundComplete"
                    @click="evaluatePlayInShootOff"
                  >
                    Runde auswerten
                  </button>
                  <button class="btn btn-sm btn-outline-secondary" @click="resetPlayInShootOff">
                    Neu starten
                  </button>
                </div>
              </template>

              <template v-else-if="playInShootOffState?.done">
                <div class="text-success small fw-bold mb-2">✅ Shoot-Off abgeschlossen!</div>
                <div
                  v-for="(t, i) in playInShootOffState.finalRanking"
                  :key="'playin-final-' + t"
                  class="d-flex align-items-center gap-2 mb-1 small"
                >
                  <span class="badge" :class="isPlayInQualifiedIndex(i) ? 'bg-success' : 'bg-danger'">
                    {{ isPlayInQualifiedIndex(i) ? 'Weiter' : 'Raus' }}
                  </span>
                  <span class="text-white">{{ t }}</span>
                </div>
                <button class="btn btn-sm btn-outline-secondary mt-2" @click="resetPlayInShootOff">
                  Wiederholen
                </button>
              </template>
            </div>
          </div>

          <div
            v-if="(playInResult.policy_notes?.length || 0) > 0"
            class="alert alert-dark border-secondary mt-3"
          >
            <ul class="mb-0">
              <li v-for="(n, i) in playInResult.policy_notes" :key="i">{{ n }}</li>
            </ul>
          </div>
        </div>

        <div class="d-flex justify-content-end">
          <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
          <button
            class="btn btn-success ms-2"
            @click="goNext"
            :disabled="!canProceedKo"
          >
            Weiter KO-Phase
          </button>
        </div>
      </div>
    </div>

    <!-- Info -->
    <div class="mt-4 p-3 border border-secondary rounded">
      <h6>ℹ️ Tiebreak-Regeln</h6>
      <p class="mb-1 text-secondary">
        <strong>3 Teams exakt gleich (Punkte + Becher-Diff + Becher+):</strong>
        Last Cup Shoot-Off — 1 Becher wird aufgestellt, alle 3 Teams werfen der Reihe nach.
        Trifft genau 1 Team: dieses Team belegt den besten Platz, die anderen 2 werfen weiter.
        Fehlt genau 1 Team: dieses Team scheidet aus (letzter Platz), die anderen 2 werfen weiter.
        Treffen oder fehlen alle: Runde wird wiederholt.
      </p>
      <p class="mb-0 text-secondary">
        <strong>Sonst:</strong> Standard-Sortierung: Punkte → Becher-Diff → Becher+.
      </p>
    </div>

    <div v-if="!allGroupsComplete" class="alert alert-dark border-warning mt-3">
      Alle Gruppenspiele muessen abgeschlossen sein, bevor KO oder Play-In gestartet werden koennen.
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, watch, nextTick } from 'vue'
import { api } from '../../api.js'
import MatchTableControls from '../MatchTableControls.vue'
import GroupStandingsTable from '../GroupStandingsTable.vue'
import { useTournamentStore } from '../../stores/tournament.js'
import {
  buildStableTableAssignmentMap,
  getAssignedActiveMatches,
  getUpcomingMatches,
  getUpcomingMatchesTotal,
  getTableNo,
  matchKey,
} from '../../utils/tableAssignments.js'

/** API-Base — Vite proxy routes /tournaments/* to Django */
const API = import.meta.env.VITE_API_BASE || ''
const store = useTournamentStore()

/** Props */
const props = defineProps({
  tournamentId: { type: Number, required: true },
  tournament: { type: Object, required: true },
  teams: { type: Array, required: true },
  teamPlayers: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['back', 'create-ko', 'update:group-matches'])

/** State */
const loading = ref(false)
const viewMode = ref('tables') // 'tables' | 'groups'
const groupMatches = ref({}) // { "Gruppe A":[{...}], ... }
const groupStandingsSrv = ref({}) // { "Gruppe A":[{...}], ... }
const lastGroupsMeta = ref([]) // { name, size, teams[] }
const playInResult = ref(null)
const playInNeeded = computed(() => !!(playInResult.value && playInResult.value.playin_needed))

const activeTableMatchId = ref(null)

/** pro Gruppe erkannter Tiebreak (nur nach Gruppen-Abschluss) */
const perGroupTiebreak = ref({}) // { "Gruppe A": { type:'LAST_CUP_ELIM', teams:[...], fixedFirst:null } }

/** Interaktiver Shoot-Off-State pro Gruppe */
const lastCupElimState = ref({})
// { "Gruppe A": { roundCount, remaining, currentRound, topPlaced, bottomPlaced, done, finalRanking, fixedFirst } }

/** Interaktiver Shoot-Off-State fuer gruppenuebergreifenden Play-In-Cutoff */
const playInShootOffState = ref(null)

const teamPlayerDrafts = ref({})
const teamPlayerSaveState = ref('idle')

/** Save-Status + Timer */
const saveState = ref('idle')
let autosaveTimer = null
const AUTOSAVE_MS = 400

/** Schützenauswahl: { mode, groupName, matchIndex, teamKey } | null */
const pendingShooter = ref(null)
const selectedPlayer = ref(null)
const draggedQueueMatchKey = ref(null)
const hoveredQueueMatchKey = ref(null)
const hoveredQueuePosition = ref(null)

/** Abschluss-Logik: { match, groupName, matchIndex, step: 'NACHWURF' | 'ALL_HIT' | 'END_QUERY' } */
const pendingConclusion = ref(null)

/** Derived */
const cupsTarget = computed(() => {
  const v = Number(props.tournament?.cupsPerGame || 6)
  return Number.isNaN(v) ? 6 : v
})
const teamsDone = computed(() => props.teams?.length || 0)
const allGroupsComplete = computed(() =>
  renderGroups.value.length > 0 &&
  renderGroups.value.every(group => isGroupComplete(group.name))
)

const dynamicTableCount = ref(null)
const activeTableCount = computed({
  get() {
    if (dynamicTableCount.value !== null) return dynamicTableCount.value
    const v = Number(props.tournament?.tableCount ?? props.tournament?.table_count)
    return Number.isNaN(v) || v < 1 ? 2 : v
  },
  set(val) {
    dynamicTableCount.value = val
  }
})

watch(activeTableCount, async (newCount) => {
  if (!props.tournamentId) return
  try {
    await api.tournaments.update(props.tournamentId, { tableCount: newCount })
    syncTableAssignments()
  } catch (e) {
    console.error('Failed to sync table count', e)
  }
})

/** Vorschau aus Teams (Fallback) */
const autoGroupsPreview = computed(() => {
  const n = props.teams.length
  const g = groupCountByBand(n)
  const names = computeGroupNames(g)
  return names.map((name, i) => {
    const inGroup = []
    for (let j = i; j < props.teams.length; j += g) inGroup.push(props.teams[j])
    return { name, teams: inGroup }
  })
})

/** Sichtbare Gruppen = Union(Meta, Matches) */
const renderGroups = computed(() => {
  const gmKeys = Object.keys(groupMatches.value)
  const meta =
    lastGroupsMeta.value?.length > 0
      ? lastGroupsMeta.value
      : autoGroupsPreview.value
  if (gmKeys.length === 0) return meta

  const allNames = Array.from(
    new Set([...meta.map(g => g.name), ...gmKeys])
  ).sort((a, b) => a.localeCompare(b, 'de'))

  return allNames.map(name => {
    const ms = groupMatches.value[name] || []
    if (ms.length > 0) {
      const set = new Set()
      for (const m of ms) {
        if (m.team1) set.add(m.team1)
        if (m.team2) set.add(m.team2)
      }
      return { name, teams: Array.from(set) }
    } else {
      const g = meta.find(x => x.name === name)
      return { name, teams: g?.teams ?? [] }
    }
  })
})

const activeMatches = computed(() =>
  getAssignedActiveMatches(groupMatches.value, activeTableCount.value)
)

const queueMatches = computed(() =>
  getUpcomingMatches(groupMatches.value, activeTableCount.value, Number.MAX_SAFE_INTEGER)
)
const upcomingMatchesTotal = computed(() =>
  getUpcomingMatchesTotal(groupMatches.value, activeTableCount.value)
)

const activeTeamNames = computed(() => {
  const teams = new Set()
  for (const match of activeMatches.value) {
    if (match.team1) teams.add(match.team1)
    if (match.team2) teams.add(match.team2)
  }
  return Array.from(teams)
})

function getMergedTeamPlayers() {
  return {
    ...(store.teamPlayers || {}),
    ...(props.teamPlayers || {}),
  }
}

function syncTeamPlayerDrafts() {
  const merged = getMergedTeamPlayers()
  const next = {}
  const names = Array.from(new Set([...(props.teams || []), ...Object.keys(merged)]))
  for (const name of names) {
    const current = merged[name] || {}
    next[name] = {
      player1: current.player1 || '',
      player2: current.player2 || '',
    }
  }
  teamPlayerDrafts.value = next
}

watch(
  () => props.tournamentId,
  () => {
    syncTeamPlayerDrafts()
  },
  { immediate: true }
)

async function saveTeamPlayersOnly() {
  if (!props.tournamentId) return
  teamPlayerSaveState.value = 'saving'
  try {
    const teamsPayload = Object.entries(teamPlayerDrafts.value || {}).map(([name, players]) => ({
      name,
      player1: (players?.player1 || '').trim(),
      player2: (players?.player2 || '').trim(),
    }))
    const result = await api.tournaments.saveTeamPlayers(props.tournamentId, teamsPayload)
    if (result?.team_players) {
      store.applyState({ team_players: result.team_players })
    }
    syncTeamPlayerDrafts()
    teamPlayerSaveState.value = 'saved'
    setTimeout(() => {
      if (teamPlayerSaveState.value === 'saved') teamPlayerSaveState.value = 'idle'
    }, 1200)
  } catch (e) {
    console.error('save-team-players failed', e)
    teamPlayerSaveState.value = 'error'
  }
}

function syncTableAssignments(shouldSave = true) {
  const desiredAssignments = buildStableTableAssignmentMap(groupMatches.value, activeTableCount.value)
  let changed = false
  const nextMatches = {}
  // Collect matches that got a fresh table assignment (null → number).
  // We persist these immediately so the backend knows before the next WebSocket
  // broadcast arrives, which prevents in-progress matches from being re-shuffled.
  const newlyAssigned = []

  for (const [groupName, matches] of Object.entries(groupMatches.value || {})) {
    nextMatches[groupName] = (matches || []).map(match => {
      const key = matchKey({ ...match, group_name: match.group_name || groupName })
      const desiredTableNo = match.winner ? null : (desiredAssignments.get(key) ?? null)
      const currentTableNo = getTableNo(match)
      if (currentTableNo === desiredTableNo) return match
      changed = true
      const updatedMatch = { ...match, table_no: desiredTableNo }
      if (!currentTableNo && desiredTableNo && !match.winner) {
        newlyAssigned.push({ groupName, match: updatedMatch })
      }
      return updatedMatch
    })
  }

  if (!changed) return false
  groupMatches.value = nextMatches
  emit('update:group-matches', groupMatches.value)
  if (shouldSave) scheduleAutoSave()

  // Immediately persist newly-assigned table numbers so the server has them
  // before the next WebSocket event can overwrite local state.
  for (const { groupName, match } of newlyAssigned) {
    _sendGroupMatch(groupName, match, { action_type: 'table_assigned' }).catch(() => {})
  }

  return true
}

/* ---------------- Backend I/O ---------------- */

async function reloadAll() {
  if (!props.tournamentId) return
  loading.value = true
  try {
    const res = await fetch(
      `${API}/tournaments/${props.tournamentId}/load-all-data`
    )
    if (!res.ok) throw new Error('load-all-data failed')
    const data = await res.json()

    const gp = data?.group_phase?.group_phase ?? data?.group_phase ?? {}
    const srvMatches = typeof gp.matches === 'object' ? gp.matches : {}
    const srvGroups = Array.isArray(gp.groups) ? gp.groups : []

    groupStandingsSrv.value = normalizeStandingsMap(
      data?.group_standings || {}
    )

    const mapped = {}
    for (const [gName, ms] of Object.entries(srvMatches)) {
      mapped[gName] = normalizeMatches(ms || {})
    }

    const metaByName = {}
    for (const g of srvGroups) {
      metaByName[g.name] = {
        name: g.name,
        teams: Array.isArray(g.teams) ? g.teams.slice() : []
      }
    }
    for (const [gName, rows] of Object.entries(groupStandingsSrv.value)) {
      if (!metaByName[gName]) {
        metaByName[gName] = { name: gName, teams: [] }
      }
      if ((metaByName[gName].teams?.length || 0) === 0) {
        metaByName[gName].teams = rows.map(r => r.name)
      }
    }
    for (const g of autoGroupsPreview.value) {
      if (!metaByName[g.name]) {
        metaByName[g.name] = {
          name: g.name,
          teams: g.teams.slice()
        }
      } else if ((metaByName[g.name].teams?.length || 0) === 0) {
        metaByName[g.name].teams = g.teams.slice()
      }
    }
    for (const old of lastGroupsMeta.value) {
      if (!metaByName[old.name]) {
        metaByName[old.name] = {
          name: old.name,
          teams: old.teams.slice()
        }
      }
      if (
        (metaByName[old.name].teams?.length || 0) <
        (old.teams?.length || 0)
      ) {
        metaByName[old.name].teams = old.teams.slice()
      }
    }

    lastGroupsMeta.value = Object.values(metaByName)
      .map(g => ({
        name: g.name,
        teams: Array.isArray(g.teams) ? g.teams : []
      }))
      .sort((a, b) => a.name.localeCompare(b.name, 'de'))

    groupMatches.value = mapped
    syncTableAssignments()

    // Tiebreaks neu berechnen – nur für abgeschlossene Gruppen
    perGroupTiebreak.value = computeAllTiebreaksForCompletedGroups()

    emit('update:group-matches', groupMatches.value)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function saveGroupPhase() {
  await saveGroupPhasePayload(buildGroupPhasePayload(groupMatches.value))
}

async function saveGroupPhasePayload(payload) {
  if (!props.tournamentId) return
  try {
    saveState.value = 'saving'
    const res = await fetch(
      `${API}/tournaments/${props.tournamentId}/save-group-phase`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    )
    if (!res.ok) throw new Error('save-group-phase failed')

    // Optimistic UI
    perGroupTiebreak.value = computeAllTiebreaksForCompletedGroups()

    saveState.value = 'saved'
    setTimeout(() => {
      if (saveState.value === 'saved') saveState.value = 'idle'
    }, 800)
  } catch (e) {
    console.error(e)
    saveState.value = 'error'
  }
}

function buildGroupPhasePayload(matchesByGroup) {
  return {
    group_phase: {
      groups: lastGroupsMeta.value.map(g => ({
        name: g.name,
        size: g.teams.length,
        teams: g.teams
      })),
      matches: Object.fromEntries(
        Object.entries(matchesByGroup || {}).map(([g, ms]) => [
          g,
          (ms || []).map(m => ({
            ...m,
            history_team1: m.history_team1 || [],
            history_team2: m.history_team2 || []
          }))
        ])
      )
    }
  }
}

/* Auto-Load */
onMounted(() => {
  reloadAll()
})
watch(
  () => props.tournamentId,
  () => {
    reloadAll()
  }
)

watch(() => store.groupPhase, (newGp) => {
  // Verhindere das Schließen von Overlays durch WebSocket-Updates
  if (pendingShooter.value || pendingConclusion.value || draggedQueueMatchKey.value) return

  if (newGp?.matches) {
    const mapped = {}
    for (const [gName, ms] of Object.entries(newGp.matches)) {
      mapped[gName] = normalizeMatches(ms)
    }
    groupMatches.value = mapped
    perGroupTiebreak.value = computeAllTiebreaksForCompletedGroups()
    computePlayInLocal()
    // Re-apply table assignments after the WebSocket update so that matches
    // finishing at Table 1 don't cause Table 2's match to migrate.
    // Any newly-assigned tables are also immediately persisted to the backend.
    syncTableAssignments(false)
  }
}, { deep: true })

watch(() => store.groupStandings, (newStandings) => {
  if (pendingShooter.value || pendingConclusion.value) return
  if (newStandings) {
    groupStandingsSrv.value = normalizeStandingsMap(newStandings)
  }
}, { deep: true })

/* Debounced Full Auto-Save */
function scheduleAutoSave() {
  if (autosaveTimer) clearTimeout(autosaveTimer)
  autosaveTimer = setTimeout(() => {
    saveGroupPhase()
  }, AUTOSAVE_MS)
}
onBeforeUnmount(() => {
  if (autosaveTimer) clearTimeout(autosaveTimer)
})

/* --------------- Gruppen/Matches --------------- */

function generateGroupsFromTeams() {
  const preview = autoGroupsPreview.value
  const nextMatches = { ...groupMatches.value }
  for (const g of preview) {
    const name = g.name
    if (!nextMatches[name] || nextMatches[name].length === 0) {
      nextMatches[name] = roundRobin(g.teams).map((m, idx) => ({
        id: `${name}-${idx + 1}`,
        group_name: name,
        team1: m[0],
        team2: m[1],
        cups_team1: 0,
        cups_team2: 0,
        winner: null,
        order_index: idx
      }))
    }
  }
  groupMatches.value = nextMatches
  syncTableAssignments(false)

  const metaBy = Object.fromEntries(
    lastGroupsMeta.value.map(g => [
      g.name,
      { ...g, teams: g.teams.slice() }
    ])
  )
  for (const g of preview) {
    if (!metaBy[g.name]) {
      metaBy[g.name] = { name: g.name, teams: g.teams.slice() }
    }
    if (metaBy[g.name].teams.length === 0) {
      metaBy[g.name].teams = g.teams.slice()
    }
  }
  lastGroupsMeta.value = Object.values(metaBy).sort((a, b) =>
    a.name.localeCompare(b.name, 'de')
  )

  emit('update:group-matches', groupMatches.value)
  scheduleAutoSave()
}

function ensureGroupMatches(group) {
  const name = group.name
  if ((groupMatches.value[name] || []).length > 0) return

  let teams = group.teams || []
  if (!teams?.length) {
    const meta = lastGroupsMeta.value.find(g => g.name === name)
    if (meta?.teams?.length) teams = meta.teams
  }
  if (!teams?.length) return

  const ms = roundRobin(teams).map((m, idx) => ({
    id: `${name}-${idx + 1}`,
    group_name: name,
    team1: m[0],
    team2: m[1],
    cups_team1: 0,
    cups_team2: 0,
    winner: null,
    order_index: idx
  }))

  groupMatches.value = { ...groupMatches.value, [name]: ms }
  syncTableAssignments(false)
  emit('update:group-matches', groupMatches.value)
  scheduleAutoSave()
}

function clearQueueDragState() {
  draggedQueueMatchKey.value = null
  hoveredQueueMatchKey.value = null
  hoveredQueuePosition.value = null
}

function onQueueDragStart(match, event) {
  const key = matchKey(match)
  draggedQueueMatchKey.value = key
  hoveredQueueMatchKey.value = key
  hoveredQueuePosition.value = 'before'
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', key)
}

function onQueueDragEnd() {
  clearQueueDragState()
}

function getQueueDropPosition(event) {
  const rect = event.currentTarget?.getBoundingClientRect?.()
  if (!rect) return 'after'
  return event.clientY < rect.top + rect.height / 2 ? 'before' : 'after'
}

function onQueueDragOver(match, event) {
  if (!draggedQueueMatchKey.value) return
  hoveredQueueMatchKey.value = matchKey(match)
  hoveredQueuePosition.value = getQueueDropPosition(event)
}

function onQueueListDragOver() {
  if (!draggedQueueMatchKey.value || !queueMatches.value.length) return
  hoveredQueueMatchKey.value = matchKey(queueMatches.value[queueMatches.value.length - 1])
  hoveredQueuePosition.value = 'after'
}

async function onQueueDrop(match, event) {
  if (!draggedQueueMatchKey.value) return
  hoveredQueueMatchKey.value = matchKey(match)
  hoveredQueuePosition.value = getQueueDropPosition(event)
  await persistQueueReorder()
}

async function onQueueListDrop() {
  if (!draggedQueueMatchKey.value) return
  if (!hoveredQueueMatchKey.value && queueMatches.value.length) {
    hoveredQueueMatchKey.value = matchKey(queueMatches.value[queueMatches.value.length - 1])
    hoveredQueuePosition.value = 'after'
  }
  await persistQueueReorder()
}

async function applyWaitingQueueOrder(reorderedWaitingMatches, options = {}) {
  const { clearDragState = true } = options
  if (!Array.isArray(reorderedWaitingMatches) || !reorderedWaitingMatches.length) {
    if (clearDragState) clearQueueDragState()
    return
  }

  const pendingOrderKeys = [
    ...activeMatches.value.map(match => matchKey(match)),
    ...reorderedWaitingMatches.map(match => matchKey(match)),
  ]
  const pendingOrderMap = new Map(
    pendingOrderKeys.map((key, idx) => [key, idx])
  )

  const nextMatches = {}
  for (const [groupName, matches] of Object.entries(groupMatches.value || {})) {
    nextMatches[groupName] = (matches || [])
      .map(match => {
        const key = matchKey({ ...match, group_name: match.group_name || groupName })
        if (match.winner || !pendingOrderMap.has(key)) return match
        const nextOrderIndex = pendingOrderMap.get(key)
        if (Number(match.order_index ?? 0) === nextOrderIndex) return match
        return { ...match, order_index: nextOrderIndex }
      })
      .sort((a, b) => Number(a.order_index ?? 0) - Number(b.order_index ?? 0))
  }

  groupMatches.value = nextMatches
  emit('update:group-matches', groupMatches.value)
  syncTableAssignments(false)
  if (clearDragState) clearQueueDragState()

  await saveGroupPhasePayload(buildGroupPhasePayload(groupMatches.value))
}

async function persistQueueReorder() {
  const draggedKey = draggedQueueMatchKey.value
  const targetKey = hoveredQueueMatchKey.value
  const targetPosition = hoveredQueuePosition.value || 'after'

  if (!draggedKey || !targetKey) {
    clearQueueDragState()
    return
  }

  const waitingMatches = queueMatches.value.slice()
  const fromIndex = waitingMatches.findIndex(match => matchKey(match) === draggedKey)
  const targetIndex = waitingMatches.findIndex(match => matchKey(match) === targetKey)

  if (fromIndex === -1 || targetIndex === -1) {
    clearQueueDragState()
    return
  }

  let insertIndex = targetIndex + (targetPosition === 'after' ? 1 : 0)
  if (fromIndex < insertIndex) insertIndex -= 1
  if (insertIndex === fromIndex) {
    clearQueueDragState()
    return
  }

  const reorderedWaitingMatches = waitingMatches.slice()
  const [movedMatch] = reorderedWaitingMatches.splice(fromIndex, 1)
  reorderedWaitingMatches.splice(insertIndex, 0, movedMatch)

  await applyWaitingQueueOrder(reorderedWaitingMatches)
}

async function moveQueueMatch(match, offset) {
  const waitingMatches = queueMatches.value.slice()
  const fromIndex = waitingMatches.findIndex(entry => matchKey(entry) === matchKey(match))
  if (fromIndex === -1) return

  const targetIndex = Math.max(0, Math.min(waitingMatches.length - 1, fromIndex + offset))
  if (targetIndex === fromIndex) return

  const reorderedWaitingMatches = waitingMatches.slice()
  const [movedMatch] = reorderedWaitingMatches.splice(fromIndex, 1)
  reorderedWaitingMatches.splice(targetIndex, 0, movedMatch)
  clearQueueDragState()
  await applyWaitingQueueOrder(reorderedWaitingMatches)
}

function buildQueueFairnessOrder(waitingMatches) {
  const remaining = waitingMatches.slice()
  const ordered = []
  const activeTeamSet = new Set(
    activeMatches.value.flatMap(match => [match.team1, match.team2]).filter(Boolean)
  )
  let lastMatchTeams = new Set()
  let previousMatchTeams = new Set()

  while (remaining.length) {
    let bestIndex = 0
    let bestScore = Infinity

    remaining.forEach((candidate, idx) => {
      const teams = [candidate.team1, candidate.team2].filter(Boolean)
      const overlapWithLast = teams.filter(team => lastMatchTeams.has(team)).length
      const overlapWithPrevious = teams.filter(team => previousMatchTeams.has(team)).length
      const overlapWithActive = teams.filter(team => activeTeamSet.has(team)).length

      const score =
        overlapWithLast * 100 +
        overlapWithPrevious * 25 +
        overlapWithActive * 12 +
        idx * 0.01

      if (score < bestScore) {
        bestScore = score
        bestIndex = idx
      }
    })

    const [chosen] = remaining.splice(bestIndex, 1)
    ordered.push(chosen)
    previousMatchTeams = lastMatchTeams
    lastMatchTeams = new Set([chosen.team1, chosen.team2].filter(Boolean))
  }

  return ordered
}

async function optimizeQueueFairness() {
  if (queueMatches.value.length < 2) return
  clearQueueDragState()
  const reorderedWaitingMatches = buildQueueFairnessOrder(queueMatches.value)
  await applyWaitingQueueOrder(reorderedWaitingMatches, { clearDragState: false })
}

/* ------------ Eingabe-Handler (lokal + Autosave) ----------- */

function toggleLiveTable(groupName, matchIndex) {
  const list = [...groupMatches.value[groupName]]
  const m = { ...list[matchIndex] }

  // Schließen, falls bereits offen
  if (activeTableMatchId.value === m.id) {
    activeTableMatchId.value = null
    return
  }

  // Initialisiere Becher-Arrays mit 'true', falls das Spiel gerade erst gestartet wird
  if (!m.cups_state_team1 || m.cups_state_team1.length === 0) {
    m.cups_state_team1 = Array(cupsTarget.value).fill(true)
  }
  if (!m.cups_state_team2 || m.cups_state_team2.length === 0) {
    m.cups_state_team2 = Array(cupsTarget.value).fill(true)
  }

  list[matchIndex] = m
  groupMatches.value[groupName] = list
  activeTableMatchId.value = m.id
}

function onLiveCupHit(groupName, matchIndex, payload) {
  const { teamKey, cupIndex } = payload
  const list = [...groupMatches.value[groupName]]
  const match = list[matchIndex]

  // Schütze ist das Team, das NICHT getroffen wurde
  const shooterTeamKey = teamKey === 'team1' ? 'team2' : 'team1'
  const shooterTeamName = shooterTeamKey === 'team1' ? match.team1 : match.team2

  const players = resolveGroupTeamPlayers(shooterTeamName)

  if (!(players.p1 || players.p2)) {
    _doLiveCupHit(groupName, matchIndex, teamKey, cupIndex, null, shooterTeamName)
    return
  }

  pendingShooter.value = {
    mode: 'cup_hit',
    matchId: match.id,
    groupName,
    matchIndex,
    teamKey,
    teamName: shooterTeamName,
    cupIndex,
    fromTable: true,
    p1: players.p1,
    p2: players.p2,
  }
  selectedPlayer.value = null
}

function _doLiveCupHit(groupName, matchIndex, teamKey, cupIndex, shooterName, shooterTeam) {
  const list = [...groupMatches.value[groupName]]
  const m = { ...list[matchIndex] }

  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'

  // Fix: Array initialisieren, falls das Spiel gerade erst gestartet wurde
  if (!m[stateKey] || !Array.isArray(m[stateKey])) {
    m[stateKey] = Array(cupsTarget.value).fill(true)
  }

  const stateArray = [...m[stateKey]]
  stateArray[cupIndex] = false
  m[stateKey] = stateArray

  const historyKey = teamKey === 'team1' ? 'hit_history_team1' : 'hit_history_team2'
  if (!m[historyKey]) m[historyKey] = []
  m[historyKey].push(cupIndex)

  const genHistoryKey = teamKey === 'team1' ? 'history_team1' : 'history_team2'
  if (!m[genHistoryKey]) m[genHistoryKey] = []
  m[genHistoryKey].push({ type: 'hit', idx: cupIndex })

  if (teamKey === 'team2') {
    m.cups_team1 = clampInt((m.cups_team1 || 0) + 1, 0, cupsTarget.value + 3) // +3 for overtime safety
  } else {
    m.cups_team2 = clampInt((m.cups_team2 || 0) + 1, 0, cupsTarget.value + 3)
  }

  // Check if ALL cups of the hit team are gone
  const standingCups = (m[stateKey] || []).filter(v => v).length

  // Beende nicht sofort, sondern starte Abschluss-Dialog wenn alle Becher weg sind
  if (standingCups === 0) {
    if (m.is_overtime) {
      // In der Verlängerung direkt zur End-Abfrage springen (kein Nachwurf mehr)
      pendingConclusion.value = { match: m, groupName, matchIndex, teamKey, step: 'END_QUERY', history: ['END_QUERY'] }
    } else {
      pendingConclusion.value = { match: m, groupName, matchIndex, teamKey, step: 'NACHWURF', history: ['NACHWURF'] }
    }
  }

  list[matchIndex] = m
  groupMatches.value[groupName] = list
  emit('update:group-matches', groupMatches.value)
  syncTableAssignments(false)

  if (isGroupComplete(groupName)) recomputePerGroupTiebreak(groupName)
  else clearGroupTiebreak(groupName)

  // teamKey is the team that LOST the cup; the shooter is the OTHER team.
  // Fallback-compute the shooter team if not explicitly passed.
  const resolvedShooterTeam = shooterTeam || (teamKey === 'team1' ? m.team2 : m.team1)
  const eventData = {
    action_type: 'cup_hit',
    team_key: teamKey,
    cup_index: cupIndex,
    player_name: shooterName,
    team_name: resolvedShooterTeam,
  }
  _sendGroupMatch(groupName, m, eventData)
  scheduleAutoSave()
}

function onLiveUndo(groupName, matchIndex, payload) {
  const { teamKey } = payload
  const list = [...groupMatches.value[groupName]]
  const m = { ...list[matchIndex] }

  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  const genHistoryKey = teamKey === 'team1' ? 'history_team1' : 'history_team2'

  // Fix: Array initialisieren, falls das Spiel gerade erst gestartet wurde
  if (!m[stateKey] || !Array.isArray(m[stateKey])) {
    m[stateKey] = Array(cupsTarget.value).fill(true)
  }

  if (m[genHistoryKey] && m[genHistoryKey].length > 0) {
    const history = [...m[genHistoryKey]]
    const lastAction = history.pop()
    m[genHistoryKey] = history

    if (lastAction.type === 'hit') {
      const restoredCupIndex = lastAction.idx
      // Becher wieder aufstellen
      m[stateKey][restoredCupIndex] = true

      // Hit-History bereinigen (parallel zur neuen History)
      const hitHistKey = teamKey === 'team1' ? 'hit_history_team1' : 'hit_history_team2'
      if (m[hitHistKey] && m[hitHistKey].length > 0) {
        const hh = [...m[hitHistKey]]
        if (hh[hh.length - 1] === restoredCupIndex) hh.pop()
        m[hitHistKey] = hh
      }

      // Punktzahl wieder abziehen
      if (teamKey === 'team2') {
        m.cups_team1 = clampInt((m.cups_team1 || 0) - 1, 0, cupsTarget.value)
      } else {
        m.cups_team2 = clampInt((m.cups_team2 || 0) - 1, 0, cupsTarget.value)
      }
    } else if (lastAction.type === 'rerack') {
      // Re-Rack rückgängig machen
      m[stateKey] = lastAction.state
      if (teamKey === 'team1') m.team1_rerack_used = false
      if (teamKey === 'team2') m.team2_rerack_used = false
    }

    applyWinnerRule(m)
    list[matchIndex] = m
    groupMatches.value[groupName] = list
    emit('update:group-matches', groupMatches.value)
    syncTableAssignments(false)

    if (isGroupComplete(groupName)) recomputePerGroupTiebreak(groupName)
    else clearGroupTiebreak(groupName)

    const eventData = { action_type: 'undo', team_key: teamKey }
    _sendGroupMatch(groupName, m, eventData)
    scheduleAutoSave()
  }
}

function onLiveRerack(groupName, matchIndex, payload) {
  const { teamKey, newState } = payload
  const list = [...groupMatches.value[groupName]]
  const m = { ...list[matchIndex] }

  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'

  // Fix: Array initialisieren, falls das Spiel gerade erst gestartet wurde
  if (!m[stateKey] || !Array.isArray(m[stateKey])) {
    m[stateKey] = Array(cupsTarget.value).fill(true)
  }

  const previousState = [...m[stateKey]]
  const genHistoryKey = teamKey === 'team1' ? 'history_team1' : 'history_team2'
  if (!m[genHistoryKey]) m[genHistoryKey] = []
  m[genHistoryKey].push({ type: 'rerack', state: previousState })

  if (teamKey === 'team1') m.team1_rerack_used = true
  if (teamKey === 'team2') m.team2_rerack_used = true
  m[stateKey] = newState

  list[matchIndex] = m
  groupMatches.value[groupName] = list
  emit('update:group-matches', groupMatches.value)

  const eventData = { action_type: 'rerack', team_key: teamKey, previous_state: JSON.stringify(previousState) }
  _sendGroupMatch(groupName, m, eventData)
  scheduleAutoSave()
}

function onLiveForfeit(groupName, matchIndex, payload) {
  const { teamKey } = payload
  const list = [...groupMatches.value[groupName]]
  const m = { ...list[matchIndex] }
  if (!m) return

  const losingTeamName = teamKey === 'team1' ? m.team1 : m.team2
  const winnerTeamName = teamKey === 'team1' ? m.team2 : m.team1
  if (!losingTeamName || !winnerTeamName) return

  m.winner = winnerTeamName
  m.status = 'done'
  m.table_no = null

  list[matchIndex] = m
  groupMatches.value[groupName] = list
  emit('update:group-matches', groupMatches.value)
  syncTableAssignments(false)

  if (pendingShooter.value?.matchId === m.id) {
    pendingShooter.value = null
    selectedPlayer.value = null
  }
  if (pendingConclusion.value?.match?.id === m.id) {
    pendingConclusion.value = null
  }
  if (activeTableMatchId.value === m.id) {
    activeTableMatchId.value = null
  }

  if (isGroupComplete(groupName)) recomputePerGroupTiebreak(groupName)
  else clearGroupTiebreak(groupName)

  _sendGroupMatch(groupName, m, {
    action_type: 'forfeit',
    team_key: teamKey,
    team_name: losingTeamName,
    winner_name: winnerTeamName,
  })
  scheduleAutoSave()
}

function setCups(groupName, matchIndex, teamField, rawValue) {
  const updated = { ...groupMatches.value }
  const list = [...(updated[groupName] || [])]
  const m = { ...list[matchIndex] }

  const v = clampInt(rawValue, 0, cupsTarget.value)
  const key = teamField === 'team1' ? 'cups_team1' : 'cups_team2'
  m[key] = v

  applyWinnerRule(m)
  list[matchIndex] = m
  updated[groupName] = list
  groupMatches.value = updated
  emit('update:group-matches', updated)
  syncTableAssignments(false)

  if (isGroupComplete(groupName)) {
    recomputePerGroupTiebreak(groupName)
  } else {
    clearGroupTiebreak(groupName)
  }
  scheduleAutoSave()
}

function resolveGroupTeamPlayers(teamName) {
  if (!teamName) return { p1: null, p2: null }
  const normalized = teamName.trim().toLowerCase()
  const mergedTeamPlayers = {
    ...(store.teamPlayers || {}),
    ...(props.teamPlayers || {}),
  }
  const allPlayerKeys = Object.keys(mergedTeamPlayers)
  const exactKey = allPlayerKeys.find(k => k.trim().toLowerCase() === normalized)
  const players = mergedTeamPlayers[exactKey || teamName] || {}
  return {
    p1: players.player1 || null,
    p2: players.player2 || null,
  }
}

function getStandingGroupCups(match, teamKey) {
  const stateKey = teamKey === 'team1' ? 'cups_state_team1' : 'cups_state_team2'
  if (Array.isArray(match?.[stateKey]) && match[stateKey].length) {
    return match[stateKey].filter(Boolean).length
  }
  const hitsTaken = teamKey === 'team1' ? safeNum(match?.cups_team2) : safeNum(match?.cups_team1)
  return Math.max(0, cupsTarget.value - hitsTaken)
}

function buildFrontOvertimeState(size) {
  const state = Array(size).fill(false)
  if (size >= 10) {
    ;[9, 7, 8].forEach(idx => { if (idx < size) state[idx] = true })
    return state
  }
  if (size >= 6) {
    ;[5, 3, 4].forEach(idx => { if (idx < size) state[idx] = true })
    return state
  }
  for (let i = Math.max(0, size - 3); i < size; i++) state[i] = true
  return state
}

function createGroupOvertimeAllocation(teamName, players, total, extra = {}) {
  return {
    mode: 'overtime_credit',
    teamName,
    p1: players.p1,
    p2: players.p2,
    bonusCupCount: total,
    bonusP1: players.p1 && !players.p2 ? total : 0,
    bonusP2: players.p2 && !players.p1 ? total : 0,
    ...extra,
  }
}

function getGroupOvertimeAssignedCups() {
  const pending = pendingShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return 0
  return Number(pending.bonusP1 || 0) + Number(pending.bonusP2 || 0)
}

function getGroupOvertimeRemainingCups() {
  const pending = pendingShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return 0
  return Math.max(0, Number(pending.bonusCupCount || 0) - getGroupOvertimeAssignedCups())
}

function isGroupOvertimeAllocationComplete() {
  const pending = pendingShooter.value
  return !!pending && pending.mode === 'overtime_credit' && getGroupOvertimeAssignedCups() > 0 && getGroupOvertimeRemainingCups() === 0
}

function adjustGroupOvertimeAllocation(slot, delta) {
  const pending = pendingShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return
  const key = slot === 'p2' ? 'bonusP2' : 'bonusP1'
  const current = Number(pending[key] || 0)
  if (delta < 0 && current <= 0) return
  if (delta > 0 && getGroupOvertimeRemainingCups() <= 0) return
  pending[key] = Math.max(0, current + delta)
}

function buildGroupOvertimeAllocations() {
  const pending = pendingShooter.value
  if (!pending || pending.mode !== 'overtime_credit') return []
  const allocations = []
  if (pending.p1 && Number(pending.bonusP1 || 0) > 0) {
    allocations.push({ player_name: pending.p1, count: Number(pending.bonusP1) })
  }
  if (pending.p2 && Number(pending.bonusP2 || 0) > 0) {
    allocations.push({ player_name: pending.p2, count: Number(pending.bonusP2) })
  }
  return allocations
}

function incrementCups(groupName, matchIndex, teamKey) {
  const match = (groupMatches.value[groupName] || [])[matchIndex]
  if (!match) return
  const teamName = teamKey === 'team1' ? match.team1 : match.team2
  const players = resolveGroupTeamPlayers(teamName)
  // If team has named players, ask who scored first
  if (players.p1 || players.p2) {
    pendingShooter.value = { mode: 'cup_hit', matchId: match.id, groupName, matchIndex, teamKey, teamName, p1: players.p1, p2: players.p2 }
    selectedPlayer.value = null
    return
  }
  _doIncrementCups(groupName, matchIndex, teamKey, null, null)
}

function selectShooter(playerName) {
  selectedPlayer.value = playerName
}

function confirmShooter() {
  if (!pendingShooter.value) return
  const { mode, groupName, matchIndex, teamKey, teamName, cupIndex, fromTable, bonusCupCount } = pendingShooter.value
  if (mode !== 'overtime_credit' && !selectedPlayer.value) return
  const playerName = selectedPlayer.value
  const allocations = mode === 'overtime_credit' ? buildGroupOvertimeAllocations() : []
  if (mode === 'overtime_credit' && (!allocations.length || !isGroupOvertimeAllocationComplete())) return

  pendingShooter.value = null
  selectedPlayer.value = null

  if (mode === 'overtime_credit') {
    applyGroupOvertime(groupName, matchIndex, teamKey, {
      teamName,
      creditCount: bonusCupCount,
      allocations,
    })
    return
  }

  if (fromTable) {
    _doLiveCupHit(groupName, matchIndex, teamKey, cupIndex, playerName, teamName)
  } else {
    _doIncrementCups(groupName, matchIndex, teamKey, playerName, teamName)
  }
}

function cancelShooter() {
  if (!pendingShooter.value) return
  pendingShooter.value = null
  selectedPlayer.value = null
}

function _doIncrementCups(groupName, matchIndex, teamKey, shooter, shooterTeam) {
  const updated = { ...groupMatches.value }
  const list = [...(updated[groupName] || [])]
  const m = { ...list[matchIndex] }

  const field = teamKey === 'team1' ? 'cups_team1' : 'cups_team2'
  // Erlaube bis zu 3 Becher mehr für die Verlängerung
  m[field] = clampInt(safeNum(m[field]) + 1, 0, cupsTarget.value + 3)

  applyWinnerRule(m)
  list[matchIndex] = m
  updated[groupName] = list
  groupMatches.value = updated
  emit('update:group-matches', updated)
  syncTableAssignments(false)

  if (isGroupComplete(groupName)) {
    recomputePerGroupTiebreak(groupName)
  } else {
    clearGroupTiebreak(groupName)
  }

  _sendGroupMatch(groupName, m, {
    action_type: 'cup_hit',
    team_key: teamKey,
    team_name: teamKey === 'team1' ? m.team1 : m.team2,
    player_name: shooter || null,
    cup_layout: cupsTarget.value,
    cup_index: null
  })
  scheduleAutoSave()
}

async function _sendGroupMatch(groupName, match, eventData) {
  if (!props.tournamentId) return
  try {
    const body = {
      group_name: groupName,
      team1: match.team1,
      team2: match.team2,
      cups_team1: match.cups_team1 ?? 0,
      cups_team2: match.cups_team2 ?? 0,
      winner: match.winner ?? null,
      order_index: match.order_index ?? 0,
      id: typeof match.id === 'number' ? match.id : null,
      cups_state_team1: match.cups_state_team1,
      cups_state_team2: match.cups_state_team2,
      hit_history_team1: match.hit_history_team1,
      hit_history_team2: match.hit_history_team2,
      history_team1: match.history_team1 || [],
      history_team2: match.history_team2 || [],
      team1_rerack_used: match.team1_rerack_used,
      team2_rerack_used: match.team2_rerack_used,
      is_overtime: !!match.is_overtime,
      table_no: getTableNo(match),
      shooter: eventData?.player_name || null,
      shooter_team: eventData?.team_name || null,
      event_data: eventData || null
    }
    await fetch(`${API}/tournaments/${props.tournamentId}/group-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch (e) {
    console.warn('group-match send failed', e)
  }
}

/* --------------- Tabellen/Play-In --------------- */

function buildTablesForAllGroups() {
  const out = {}
  for (const g of renderGroups.value.map(x => x.name)) {
    out[g] = getFinalStandings(g)
  }
  return out
}
function recalculateTables() {
  for (const g of renderGroups.value.map(x => x.name)) {
    if (isGroupComplete(g)) recomputePerGroupTiebreak(g)
    else clearGroupTiebreak(g)
  }
  if (playInResult.value) computePlayInLocal()
}

function chooseKoSize(qualified) {
  if (qualified <= 0) return 0
  const sizes = [4, 8, 16, 32, 64, 128]
  for (const k of sizes) if (k >= qualified) return k
  return qualified
}

function normalizeRankingCandidate(row) {
  return {
    name: String(row?.name || ''),
    points: Number(row?.points || 0),
    cupsDiff: Number(
      (row?.cupsDiff ?? (row?.cupsFor || 0) - (row?.cupsAgainst || 0)) || 0
    ),
    cupsFor: Number(row?.cupsFor || 0)
  }
}

function compareRankingCandidates(a, b) {
  if (b.points !== a.points) return b.points - a.points
  if (b.cupsDiff !== a.cupsDiff) return b.cupsDiff - a.cupsDiff
  if (b.cupsFor !== a.cupsFor) return b.cupsFor - a.cupsFor
  return 0
}

function equalRankingMetrics(x, y) {
  return !!(
    x &&
    y &&
    x.points === y.points &&
    x.cupsDiff === y.cupsDiff &&
    x.cupsFor === y.cupsFor
  )
}

function buildShootOffPlan(teams, options = {}) {
  return {
    group: options.group || 'Shoot-Off',
    type: 'LAST_CUP_ELIM',
    teams: teams.slice(),
    fixedFirst: options.fixedFirst ?? null,
    qualifyingSlots: options.qualifyingSlots ?? null,
    note:
      options.note ||
      '1 Becher, alle Teams werfen nacheinander. Wer allein nicht trifft, scheidet aus.'
  }
}

function sameShootOffTeams(state, plan) {
  if (!state || !plan) return false
  const left = (state.sourceTeams || []).slice().sort((a, b) => a.localeCompare(b, 'de'))
  const right = (plan.teams || []).slice().sort((a, b) => a.localeCompare(b, 'de'))
  return left.length === right.length && left.every((team, idx) => team === right[idx])
}

function createShootOffState(plan) {
  return {
    sourceTeams: plan.teams.slice(),
    roundCount: 1,
    remaining: plan.teams.slice(),
    currentRound: Object.fromEntries(plan.teams.map(team => [team, null])),
    topPlaced: [],
    bottomPlaced: [],
    done: false,
    finalRanking: [],
    fixedFirst: plan.fixedFirst ?? null,
    qualifyingSlots: plan.qualifyingSlots ?? null,
  }
}

function nextShootOffState(state) {
  if (!state || state.done) return state
  const hitters = state.remaining.filter(team => state.currentRound[team] === 'hit')
  const missers = state.remaining.filter(team => state.currentRound[team] === 'miss')

  if (hitters.length === 0 || missers.length === 0) {
    return {
      ...state,
      roundCount: state.roundCount + 1,
      currentRound: Object.fromEntries(state.remaining.map(team => [team, null]))
    }
  }

  let newTopPlaced = [...state.topPlaced]
  let newBottomPlaced = [...state.bottomPlaced]
  let newRemaining = []

  if (hitters.length === 1) {
    newTopPlaced = [...newTopPlaced, hitters[0]]
    newRemaining = missers
  } else {
    newBottomPlaced = [...newBottomPlaced, missers[0]]
    newRemaining = hitters
  }

  const done = newRemaining.length <= 1
  const finalRanking = done
    ? [...newTopPlaced, ...newRemaining, ...newBottomPlaced.slice().reverse()]
    : []

  return {
    ...state,
    topPlaced: newTopPlaced,
    bottomPlaced: newBottomPlaced,
    remaining: newRemaining,
    roundCount: state.roundCount + 1,
    currentRound: done ? {} : Object.fromEntries(newRemaining.map(team => [team, null])),
    done,
    finalRanking
  }
}

function buildPlayInResult() {
  const tables = buildTablesForAllGroups()
  const groupNames = Object.keys(tables)
  const directQualified = []
  const thirdPlaces = []
  const fourthPlaces = []

  const tiebreakPlans = []
  const rageCageGroups = []

  const sizeByGroup = {}
  for (const g of renderGroups.value) sizeByGroup[g.name] = g.teams.length

  if (!allGroupsComplete.value) {
    return {
      ready_for_knockout: false,
      playin_needed: false,
      ko_size: 0,
      direct_qualified: [],
      auto_advanced: [],
      ranking_candidates: [],
      tiebreaks: [],
      rage_cage_groups: [],
      playin_matches: [],
      last_cup_shootoff: null,
      policy_notes: [
        'Noch nicht alle Gruppenspiele sind abgeschlossen.'
      ]
    }
  }

  for (const g of groupNames) {
    const rows = tables[g] || []
    const plan = detectGroupTiebreak(g, rows)
    if (plan) tiebreakPlans.push(plan)

    if (!plan) {
      if (rows[0]) directQualified.push(rows[0].name)
      if (rows[1]) directQualified.push(rows[1].name)
      if (rows[2]) thirdPlaces.push(rows[2])
      if (rows[3]) fourthPlaces.push(rows[3])
      continue
    }

    if (plan.fixedFirst) {
      directQualified.push(plan.fixedFirst)
    }
  }

  const potentialQualified = groupNames.reduce(
    (count, groupName) => count + Math.min(2, (tables[groupName] || []).length),
    0
  )
  const koSize = chooseKoSize(potentialQualified)
  const slotsNeeded = Math.max(0, koSize - directQualified.length)

  const notes = []
  notes.push(
    `Es werden ${slotsNeeded} zusätzliche Platz/Plätze benötigt, um auf ${koSize} KO-Teams zu kommen.`
  )

  if (tiebreakPlans.length > 0) {
    return {
      ready_for_knockout: false,
      playin_needed: false,
      ko_size: koSize,
      direct_qualified: directQualified,
      auto_advanced: [],
      ranking_candidates: [],
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      playin_matches: [],
      last_cup_shootoff: null,
      policy_notes: [
        'Es gibt noch offene gruppeninterne Last Cup Shoot-Offs.',
        ...notes,
      ]
    }
  }

  if (slotsNeeded === 0) {
    return {
      ready_for_knockout: true,
      playin_needed: false,
      ko_size: koSize,
      direct_qualified: directQualified,
      auto_advanced: [],
      ranking_candidates: [],
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      playin_matches: [],
      last_cup_shootoff: null,
      policy_notes: ['Kein Play-In nötig – alle Plätze gefüllt.']
    }
  }

  const allAreTrios = groupNames.every(
    g => (sizeByGroup[g] || 0) === 3
  )
  let candidateRows = []
  if (allAreTrios) {
    candidateRows = thirdPlaces.slice()
  } else {
    candidateRows = thirdPlaces.slice()
    if (candidateRows.length < slotsNeeded + 1) {
      candidateRows = candidateRows.concat(fourthPlaces)
    }
  }

  const candidates = candidateRows
    .filter(Boolean)
    .map(normalizeRankingCandidate)
    .sort(compareRankingCandidates)

  if (candidates.length < slotsNeeded) {
    return {
      ready_for_knockout: true,
      playin_needed: true,
      ko_size: koSize,
      direct_qualified: directQualified,
      ranking_candidates: candidates,
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      playin_matches: [],
      last_cup_shootoff: null,
      policy_notes: [
        ...notes,
        'Zu wenige Kandidaten vorhanden – bitte manuell entscheiden (Sonderverfahren).'
      ]
    }
  }

  const need = slotsNeeded
  const k = need - 1
  const cutoffTie =
    need > 0 &&
    k >= 0 &&
    k < candidates.length - 1 &&
    equalRankingMetrics(candidates[k], candidates[k + 1])

  // Kein Gleichstand am Cut-Off → automatisch weiter
  if (!cutoffTie) {
    const auto = candidates.slice(0, need).map(x => x.name)
    return {
      ready_for_knockout: true,
      playin_needed: false,
      ko_size: koSize,
      direct_qualified: directQualified,
      auto_advanced: auto,
      ranking_candidates: candidates,
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      playin_matches: [],
      last_cup_shootoff: null,
      policy_notes: [
        ...notes,
        `Kein Gleichstand am Cut-Off → automatisch weiter: ${auto.join(', ')}.`
      ]
    }
  }

  // Gleichstand am Cut-Off → Verfahren je Größe der Tie-Range
  let s = k
  let e = k + 1
  while (s - 1 >= 0 && equalRankingMetrics(candidates[s - 1], candidates[k])) s--
  while (e + 1 < candidates.length && equalRankingMetrics(candidates[e + 1], candidates[k]))
    e++
  const tieRange = candidates.slice(s, e + 1)

  const playin_matches = []
  const rage_cutoff_groups = []
  const shootOffPlan =
    tieRange.length >= 3 && tieRange.length === slotsNeeded + 1
      ? buildShootOffPlan(tieRange.map(team => team.name), {
          group: 'Play-In Cut-Off',
          qualifyingSlots: slotsNeeded,
          note: `Es muss genau ein letzter Platz zwischen ${tieRange.length} Teams bestimmt werden. Daher wird ein Last Cup Shoot-Off gespielt; die besten ${slotsNeeded} Teams qualifizieren sich fuer die KO-Phase.`
        })
      : null

  if (shootOffPlan) {
    const stateMatches = sameShootOffTeams(playInShootOffState.value, shootOffPlan)
    if (stateMatches && playInShootOffState.value?.done) {
      const auto = playInShootOffState.value.finalRanking.slice(0, slotsNeeded)
      return {
        ready_for_knockout: true,
        playin_needed: false,
        ko_size: koSize,
        direct_qualified: directQualified,
        auto_advanced: auto,
        ranking_candidates: candidates,
        tiebreaks: tiebreakPlans,
        rage_cage_groups: rageCageGroups,
        playin_matches: [],
        last_cup_shootoff: null,
        policy_notes: [
          ...notes,
          `Last Cup Shoot-Off entschieden: ${auto.join(', ')} qualifizieren sich.`
        ]
      }
    }

    return {
      ready_for_knockout: false,
      playin_needed: true,
      ko_size: koSize,
      direct_qualified: directQualified,
      auto_advanced: [],
      ranking_candidates: candidates,
      tie_range: tieRange,
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      playin_matches: [],
      last_cup_shootoff: shootOffPlan,
      policy_notes: [
        ...notes,
        'Am Play-In-Cut-Off ist kein letzter Platz eindeutig bestimmbar. Der Last Cup Shoot-Off muss vor dem Weitergehen abgeschlossen werden.'
      ]
    }
  }

  if (tieRange.length === 2) {
    playin_matches.push({
      match_id: 1,
      team1: tieRange[0].name,
      team2: tieRange[1].name,
      cups_per_game: 3
    })
    notes.push(
      'Exakter 2er-Gleichstand am Cut-Off → 1× 1-gegen-1 (3 Becher).'
    )
  } else if (tieRange.length === 3) {
    rage_cutoff_groups.push({
      group: 'Cut-Off',
      teams: tieRange.map(t => t.name),
      note: '3er-Gleichstand: Rage Cage – Letzter scheidet aus.'
    })
    notes.push(
      '3er-Gleichstand am Cut-Off → Rage Cage (1 Team scheidet aus).'
    )
  } else if (tieRange.length === 4) {
    for (let i = 0; i < 4; i += 2) {
      playin_matches.push({
        match_id: i / 2 + 1,
        team1: tieRange[i].name,
        team2: tieRange[i + 1].name,
        cups_per_game: 3
      })
    }
    notes.push(
      '4er-Gleichstand am Cut-Off → 2× 1-gegen-1 (3 Becher), Gewinner weiter.'
    )
  } else if (tieRange.length >= 5) {
    notes.push(
      '5er-Gleichstand am Cut-Off → „Elfmeter“-Modus empfohlen; manuelle Auswahl erforderlich.'
    )
  }

  return {
    ready_for_knockout: true,
    playin_needed: true,
    ko_size: koSize,
    direct_qualified: directQualified,
    ranking_candidates: candidates,
    tie_range: tieRange,
    tiebreaks: tiebreakPlans,
    rage_cage_groups: [...rageCageGroups, ...rage_cutoff_groups],
    playin_matches,
    last_cup_shootoff: null,
    policy_notes: notes
  }
}

function computePlayInLocal() {
  playInResult.value = buildPlayInResult()
  return playInResult.value
}

const activePlayInShootOffPlan = computed(
  () => playInResult.value?.last_cup_shootoff ?? buildPlayInResult().last_cup_shootoff ?? null
)

const isPlayInShootOffRoundComplete = computed(() => {
  const state = playInShootOffState.value
  if (!state || state.done) return false
  return state.remaining.every(team => state.currentRound[team] !== null)
})

/** Weiter */
const canProceedKo = computed(() => allGroupsComplete.value && (playInResult.value?.ready_for_knockout || false))
function goNext() {
  const playInPlan = playInResult.value
  if (!playInPlan?.ready_for_knockout) return
  const tables = buildTablesForAllGroups()
  emit('create-ko', {
    tables,
    playIn: playInPlan || null,
    koSize: playInPlan.ko_size
  })
}

/* ---------------- Utils ---------------- */

function normalizeMatches(list) {
  return (list || []).map((m, idx) => ({
    id: m.id ?? `${m.group_name || 'G'}-${idx + 1}`,
    group_name: m.group_name ?? guessGroupNameFromId(m.id) ?? '',
    team1: m.team1,
    team2: m.team2,
    cups_team1: Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0,
    cups_team2: Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0,
    winner: m.winner ?? null,
    order_index: m.order_index ?? idx,
    cups_state_team1: Array.isArray(m.cups_state_team1) && m.cups_state_team1.length > 0 ? m.cups_state_team1 : null,
    cups_state_team2: Array.isArray(m.cups_state_team2) && m.cups_state_team2.length > 0 ? m.cups_state_team2 : null,
    hit_history_team1: Array.isArray(m.hit_history_team1) ? m.hit_history_team1 : [],
    hit_history_team2: Array.isArray(m.hit_history_team2) ? m.hit_history_team2 : [],
    history_team1: Array.isArray(m.history_team1) ? m.history_team1 : [],
    history_team2: Array.isArray(m.history_team2) ? m.history_team2 : [],
    team1_rerack_used: !!m.team1_rerack_used,
    team2_rerack_used: !!m.team2_rerack_used,
    is_overtime: !!m.is_overtime,
    table_no: getTableNo(m)
  }))
}

function normalizeStandingsMap(obj) {
  const pick = (src, keys, fallback = 0) => {
    for (const k of keys) {
      if (src[k] !== undefined && src[k] !== null) return src[k]
    }
    return fallback
  }
  const out = {}
  for (const [g, rows] of Object.entries(obj || {})) {
    out[g] = (rows || []).map(r => ({
      name: String(pick(r, ['name', 'team', 'team_name'], '')),
      wins: Number.isFinite(+pick(r, ['wins', 'win', 'games_won', 'w'])) ? +pick(r, ['wins', 'win', 'games_won', 'w']) : 0,
      losses: Number.isFinite(+pick(r, ['losses', 'loss', 'games_lost', 'l'])) ? +pick(r, ['losses', 'loss', 'games_lost', 'l']) : 0,
      points: Number.isFinite(+pick(r, ['points', 'pts', 'score'])) ? +pick(r, ['points', 'pts', 'score']) : 0,
      cupsFor: Number.isFinite(+pick(r, ['cupsFor', 'cups_for', 'cupsPlus', 'cups_plus', 'cups'], 0))
        ? +pick(r, ['cupsFor', 'cups_for', 'cupsPlus', 'cups_plus', 'cups'], 0)
        : 0,
      cupsAgainst: Number.isFinite(+pick(r, ['cupsAgainst', 'cups_against', 'cupsMinus', 'cups_minus'], 0))
        ? +pick(r, ['cupsAgainst', 'cups_against', 'cupsMinus', 'cups_minus'], 0)
        : 0,
      cupsDiff: Number.isFinite(+pick(r, ['cupsDiff', 'cups_diff'], NaN))
        ? +pick(r, ['cupsDiff', 'cups_diff'], NaN)
        : Number(pick(r, ['cupsFor', 'cups_for', 'cupsPlus', 'cups_plus', 'cups'], 0)) -
          Number(pick(r, ['cupsAgainst', 'cups_against', 'cupsMinus', 'cups_minus'], 0))
    }))
    // Punkte ableiten, falls Backend keine liefert (Standard: 2 pro Sieg)
    out[g] = out[g].map(row => ({
      ...row,
      points: Number.isFinite(row.points) && row.points > 0 ? row.points : row.wins * 2
    }))
  }
  return out
}

function guessGroupNameFromId(id) {
  if (!id || typeof id !== 'string') return null
  const m = id.match(/^(Gruppe [A-Z])/)
  return m ? m[1] : null
}
function roundRobin(arr) {
  const a = (arr || []).filter(Boolean)
  if (a.length < 2) return []

  const teams = [...a]
  if (teams.length % 2 !== 0) teams.push(null) // Virtuelles Freilos bei ungerader Anzahl

  const totalRounds = teams.length - 1
  const matchesPerRound = teams.length / 2
  const ms = []
  for (let round = 0; round < totalRounds; round++) {
    for (let match = 0; match < matchesPerRound; match++) {
      const t1 = teams[match]
      const t2 = teams[teams.length - 1 - match]
      if (t1 !== null && t2 !== null) ms.push([t1, t2])
    }
    // Rotation: Das erste Team bleibt fixiert, die anderen rotieren durch
    teams.splice(1, 0, teams.pop())
  }
  return ms
}
function groupCountByBand(n) {
  if (n <= 4) return 1
  if (n <= 8) return 2
  if (n <= 11) return 3
  if (n <= 16) return 4
  return Math.max(4, Math.round(n / 4.5))
}
function computeGroupNames(g) {
  return Array.from({ length: g }, (_, i) => `Gruppe ${String.fromCharCode(65 + i)}`)
}

/* ----- Abschluss-Logik & Tiebreak nur bei vollständiger Gruppe ----- */

function expectedMatchCountForGroup(groupName) {
  const fromMatches = new Set()
  for (const m of groupMatches.value[groupName] || []) {
    if (m.team1) fromMatches.add(m.team1)
    if (m.team2) fromMatches.add(m.team2)
  }
  let teams = Array.from(fromMatches)
  if (teams.length === 0) {
    const meta = lastGroupsMeta.value.find(g => g.name === groupName)
    if (meta?.teams?.length) teams = meta.teams.slice()
  }
  if (teams.length === 0) {
    const preview = autoGroupsPreview.value.find(g => g.name === groupName)
    if (preview?.teams?.length) teams = preview.teams.slice()
  }
  const n = teams.length
  return n > 1 ? (n * (n - 1)) / 2 : 0
}

function isGroupComplete(groupName) {
  const ms = groupMatches.value[groupName] || []
  const expected = expectedMatchCountForGroup(groupName)
  if (ms.length < expected || expected === 0) return false
  return ms.every(m => !!m.winner)
}

function computeAllTiebreaksForCompletedGroups() {
  const next = {}
  const names = Array.from(
    new Set([
      ...Object.keys(groupMatches.value),
      ...lastGroupsMeta.value.map(g => g.name)
    ])
  )
  for (const g of names) {
    if (!isGroupComplete(g)) continue
    const rows = getFinalStandings(g)
    const plan = detectGroupTiebreak(g, rows)
    if (plan) next[g] = plan
  }
  return next
}

function getFinalStandings(groupName) {
  let arr
  const matches = groupMatches.value[groupName] || []
  if (matches.length > 0) {
    arr = computeGroupTable(matches)
  } else {
    const srv = groupStandingsSrv.value[groupName]
    if (Array.isArray(srv) && srv.length > 0) {
      arr = srv
    } else {
      const meta = lastGroupsMeta.value.find(g => g.name === groupName)
      const teams = meta?.teams ?? []
      arr = teams.map(name => ({
        name, wins: 0, losses: 0, points: 0, cupsFor: 0, cupsAgainst: 0, cupsDiff: 0
      }))
    }
  }

  // Shoot-Off-Ergebnis einarbeiten
  const elimState = lastCupElimState.value[groupName]
  if (elimState?.done && elimState.finalRanking?.length > 0) {
    return applyElimOverride(arr, elimState.finalRanking)
  }
  return arr
}

function applyElimOverride(standings, finalRanking) {
  const rankedSet = new Set(finalRanking)
  const byName = new Map(standings.map(r => [r.name, r]))
  let rankIdx = 0
  return standings.map(row =>
    rankedSet.has(row.name) ? (byName.get(finalRanking[rankIdx++]) ?? row) : row
  )
}

function computeGroupTable(matches) {
  const rows = new Map()
  const ensure = name => {
    if (!rows.has(name)) {
      rows.set(name, {
        name,
        wins: 0,
        losses: 0,
        points: 0,
        cupsFor: 0,
        cupsAgainst: 0,
        cupsDiff: 0
      })
    }
    return rows.get(name)
  }
  for (const m of matches) {
    if (!m.team1 || !m.team2) continue
    const a = ensure(m.team1)
    const b = ensure(m.team2)
    const c1 = Number(m.cups_team1 || 0)
    const c2 = Number(m.cups_team2 || 0)
    a.cupsFor += c1
    a.cupsAgainst += c2
    b.cupsFor += c2
    b.cupsAgainst += c1
    if (m.winner === m.team1) {
      a.wins++
      b.losses++
      a.points += 2
    } else if (m.winner === m.team2) {
      b.wins++
      a.losses++
      b.points += 2
    }
  }
  for (const r of rows.values()) {
    r.cupsDiff = r.cupsFor - r.cupsAgainst
  }
  const arr = Array.from(rows.values()).sort((x, y) => {
    if (y.points !== x.points) return y.points - x.points
    if (y.cupsDiff !== x.cupsDiff) return y.cupsDiff - x.cupsDiff
    if (y.cupsFor !== x.cupsFor) return y.cupsFor - x.cupsFor
    return 0
  })
  return arr
}

function getRowClass(groupName, idx) {
  if (markTiebreak(groupName, idx)) return 'table-warning'
  return idx < 2 ? 'table-success' : playInNeeded.value ? 'table-warning' : ''
}

function statusLabel(groupName, idx) {
  if (markTiebreak(groupName, idx)) return 'Tiebreak'
  if (idx < 2) return 'Direkt'
  return playInNeeded.value ? 'Play-In' : '—'
}

function statusBadge(groupName, idx) {
  if (markTiebreak(groupName, idx)) return 'bg-warning text-dark'
  if (idx < 2) return 'bg-success'
  if (playInNeeded.value) return 'bg-warning text-dark'
  return 'bg-secondary'
}

function standingStatus(groupName, idx) {
  const hasTiebreak = markTiebreak(groupName, idx)
  return {
    label: statusLabel(groupName, idx),
    badgeClass: statusBadge(groupName, idx),
    rowClass: getRowClass(groupName, idx),
    tagLabel: hasTiebreak ? 'TB' : '',
    tagClass: hasTiebreak ? 'bg-warning text-dark' : '',
    tagTitle: hasTiebreak ? 'Teil der Tiebreak-Konstellation' : '',
  }
}

function safeNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function conclusionStep(newStep) {
  if (!pendingConclusion.value) return
  pendingConclusion.value.step = newStep
  if (!pendingConclusion.value.history) pendingConclusion.value.history = []
  pendingConclusion.value.history.push(newStep)
}

function conclusionBack() {
  if (!pendingConclusion.value || !pendingConclusion.value.history) return
  const h = pendingConclusion.value.history
  if (h.length <= 1) {
    pendingConclusion.value = null
    return
  }
  h.pop() // remove current
  pendingConclusion.value.step = h[h.length - 1]
}

function finishConclusion(actuallyFinish) {
  if (!pendingConclusion.value) return
  const { match, groupName, matchIndex } = pendingConclusion.value

  if (actuallyFinish) {
    // Finaler Sieg
    const a = safeNum(match.cups_team1)
    const b = safeNum(match.cups_team2)
    if (a === b) {
      return
    }
    match.winner = a > b ? match.team1 : match.team2

    const list = [...groupMatches.value[groupName]]
    list[matchIndex] = match
    groupMatches.value[groupName] = list
    syncTableAssignments(false)
    _sendGroupMatch(groupName, match, { action_type: 'finished' })
    scheduleAutoSave()
  }

  pendingConclusion.value = null
}

function conclusionOvertime() {
  if (!pendingConclusion.value) return
  const { groupName, matchIndex, teamKey } = pendingConclusion.value
  const list = [...groupMatches.value[groupName]]
  const match = { ...list[matchIndex] }
  if (!match) return
  const overtimeTeamName = teamKey === 'team1' ? match.team1 : match.team2
  const opponentTeamKey = teamKey === 'team1' ? 'team2' : 'team1'
  const remainingOpponentCups = getStandingGroupCups(match, opponentTeamKey)

  if (remainingOpponentCups > 0) {
    const players = resolveGroupTeamPlayers(overtimeTeamName)
    if (players.p1 || players.p2) {
      pendingShooter.value = createGroupOvertimeAllocation(overtimeTeamName, players, remainingOpponentCups, {
        matchId: match.id,
        groupName,
        matchIndex,
        teamKey,
      })
      selectedPlayer.value = null
      return
    }
  }

  applyGroupOvertime(groupName, matchIndex, teamKey, {
    playerName: null,
    teamName: overtimeTeamName,
    creditCount: remainingOpponentCups,
  })
}

function applyGroupOvertime(groupName, matchIndex, teamKey, creditInfo = null) {
  const list = [...groupMatches.value[groupName]]
  const match = { ...list[matchIndex] }
  if (!match) return

  if (creditInfo?.creditCount > 0) {
    const scoreField = teamKey === 'team1' ? 'cups_team1' : 'cups_team2'
    match[scoreField] = clampInt(
      safeNum(match[scoreField]) + creditInfo.creditCount,
      0,
      cupsTarget.value
    )
  }

  // Verlängerung startet mit 3 Bechern im vorderen Dreieck.
  const newState = buildFrontOvertimeState(cupsTarget.value)

  match.cups_state_team1 = [...newState]
  match.cups_state_team2 = [...newState]
  // Wir setzen die Punkte NICHT zurück, sondern lassen sie bei 6 (bzw. 10)
  // Damit zählen sie bis 9 (bzw. 13) hoch, was für die Tabelle korrekt ist.
  match.winner = null
  match.is_overtime = true

  list[matchIndex] = match
  groupMatches.value[groupName] = list
  syncTableAssignments(false)

  _sendGroupMatch(groupName, match, creditInfo?.teamName && Array.isArray(creditInfo?.allocations) && creditInfo.allocations.length
    ? {
        action_type: 'overtime_credit',
        team_name: creditInfo.teamName,
        credit_count: creditInfo.creditCount,
        credit_allocations: creditInfo.allocations,
      }
    : { action_type: 'overtime' })
  scheduleAutoSave()
  pendingConclusion.value = null
}

function clampInt(v, min, max) {
  const n = parseInt(v, 10)
  const num = Number.isFinite(n) ? n : 0
  return Math.max(min, Math.min(max, num))
}
function applyWinnerRule(m) {
  const a = safeNum(m.cups_team1)
  const b = safeNum(m.cups_team2)
  const target = m.is_overtime ? cupsTarget.value + 3 : cupsTarget.value
  if (a >= target || b >= target) {
    if (a !== b) m.winner = a > b ? m.team1 : m.team2
  } else if (a === b) {
    m.winner = null
  }
}

/* ---------- Tiebreak-Erkennung ---------- */

function equalTripleByPointsDiff([r1, r2, r3]) {
  if (!r1 || !r2 || !r3) return false
  return (
    r1.points === r2.points &&
    r2.points === r3.points &&
    r1.cupsDiff === r2.cupsDiff &&
    r2.cupsDiff === r3.cupsDiff &&
    r1.cupsFor === r2.cupsFor &&
    r2.cupsFor === r3.cupsFor
  )
}

function detectGroupTiebreak(groupName, standings) {
  // Shoot-Off bereits aufgelöst → kein Tiebreak mehr
  if (lastCupElimState.value[groupName]?.done) return null

  const meta = lastGroupsMeta.value.find(g => g.name === groupName)
  const size = meta?.teams?.length || standings.length

  if (size === 3 && standings.length >= 3) {
    const [t1, t2, t3] = standings
    if (equalTripleByPointsDiff([t1, t2, t3])) {
      return {
        group: groupName,
        type: 'LAST_CUP_ELIM',
        teams: [t1.name, t2.name, t3.name],
        fixedFirst: null
      }
    }
  }

  if (size === 4 && standings.length >= 4) {
    const [t1, t2, t3, t4] = standings

    const topThreeTied =
      equalTripleByPointsDiff([t1, t2, t3]) &&
      !equalRankingMetrics(t3, t4)

    if (topThreeTied) {
      return {
        group: groupName,
        type: 'LAST_CUP_ELIM',
        teams: [t1.name, t2.name, t3.name],
        fixedFirst: null
      }
    }

    const bottomThreeTied =
      equalTripleByPointsDiff([t2, t3, t4]) &&
      !equalRankingMetrics(t1, t2)

    if (bottomThreeTied) {
      return {
        group: groupName,
        type: 'LAST_CUP_ELIM',
        teams: [t2.name, t3.name, t4.name],
        fixedFirst: t1.name
      }
    }
  }
  return null
}

function recomputePerGroupTiebreak(groupName) {
  const rows = getFinalStandings(groupName)
  const plan = detectGroupTiebreak(groupName, rows)
  const next = { ...perGroupTiebreak.value }
  if (plan) next[groupName] = plan
  else delete next[groupName]
  perGroupTiebreak.value = next
}

function clearGroupTiebreak(groupName) {
  if (!perGroupTiebreak.value[groupName]) return
  const next = { ...perGroupTiebreak.value }
  delete next[groupName]
  perGroupTiebreak.value = next
}

/* ---------- Last Cup Shoot-Off ---------- */

function startLastCupElim(groupName) {
  const plan = perGroupTiebreak.value[groupName]
  if (!plan || plan.type !== 'LAST_CUP_ELIM') return
  lastCupElimState.value = {
    ...lastCupElimState.value,
    [groupName]: createShootOffState(plan)
  }
  computePlayInLocal()
}

function setElimResult(groupName, teamName, result) {
  const state = lastCupElimState.value[groupName]
  if (!state || state.done) return
  lastCupElimState.value = {
    ...lastCupElimState.value,
    [groupName]: { ...state, currentRound: { ...state.currentRound, [teamName]: result } }
  }
}

function isElimRoundComplete(groupName) {
  const state = lastCupElimState.value[groupName]
  if (!state || state.done) return false
  return state.remaining.every(t => state.currentRound[t] !== null)
}

function evaluateElimRound(groupName) {
  const state = lastCupElimState.value[groupName]
  if (!state || state.done || !isElimRoundComplete(groupName)) return
  const nextState = nextShootOffState(state)

  // Wenn fertig: Tiebreak-Plan entfernen (detectGroupTiebreak gibt jetzt null zurück)
  if (nextState.done) {
    const next = { ...perGroupTiebreak.value }
    delete next[groupName]
    perGroupTiebreak.value = next
  }

  lastCupElimState.value = {
    ...lastCupElimState.value,
    [groupName]: nextState
  }
  computePlayInLocal()
}

function resetElim(groupName) {
  const next = { ...lastCupElimState.value }
  delete next[groupName]
  lastCupElimState.value = next
  recomputePerGroupTiebreak(groupName)
  computePlayInLocal()
}

function startPlayInShootOff() {
  if (!activePlayInShootOffPlan.value) return
  playInShootOffState.value = createShootOffState(activePlayInShootOffPlan.value)
  computePlayInLocal()
}

function setPlayInShootOffResult(teamName, result) {
  const state = playInShootOffState.value
  if (!state || state.done) return
  playInShootOffState.value = {
    ...state,
    currentRound: { ...state.currentRound, [teamName]: result }
  }
}

function evaluatePlayInShootOff() {
  const state = playInShootOffState.value
  if (!state || state.done || !isPlayInShootOffRoundComplete.value) return
  playInShootOffState.value = nextShootOffState(state)
  computePlayInLocal()
}

function resetPlayInShootOff() {
  const sourcePlan = activePlayInShootOffPlan.value || (playInShootOffState.value
    ? buildShootOffPlan(playInShootOffState.value.sourceTeams || [], {
        group: 'Play-In Cut-Off',
        qualifyingSlots: playInShootOffState.value.qualifyingSlots ?? null,
        note: 'Shoot-Off wurde zur erneuten Ausspielung zurueckgesetzt.'
      })
    : null)
  playInShootOffState.value = sourcePlan ? createShootOffState(sourcePlan) : null
  computePlayInLocal()
}

function isPlayInQualifiedIndex(idx) {
  const plan = playInResult.value
  if (!plan) return false
  const slotsAvailable = Math.max(0, (plan.ko_size || 0) - (plan.direct_qualified?.length || 0))
  return idx < slotsAvailable
}

function markTiebreak(groupName, idxInSortedTable) {
  const tb = perGroupTiebreak.value[groupName]
  if (!tb) return false
  if (tb.type === 'LAST_CUP_ELIM') {
    const tiedSet = new Set(tb.teams)
    const rows = getFinalStandings(groupName)
    return tiedSet.has(rows[idxInSortedTable]?.name)
  }
  return false
}

/** Teamnamen kürzen */
function formatTeamName(name, maxChars = 5) {
  const s = String(name || '').trim()
  if (s.length <= maxChars) return s
  if (maxChars <= 3) return s.slice(0, maxChars)
  return s.slice(0, maxChars - 1) + '…'
}

function formatPlayers(teamName) {
  const normalized = String(teamName || '').trim().toLowerCase()
  const mergedTeamPlayers = {
    ...(store.teamPlayers || {}),
    ...(props.teamPlayers || {}),
  }
  const exactKey = Object.keys(mergedTeamPlayers).find(k => k.trim().toLowerCase() === normalized)
  const p = mergedTeamPlayers[exactKey || teamName]
  if (!p) return ''
  if (p.player1 && p.player2) return `${p.player1} & ${p.player2}`
  return p.player1 || p.player2 || ''
}
</script>

<style scoped>
.match-entry {
  background: rgba(255, 255, 255, 0.05);
}

.group-queue-card {
  overflow: hidden;
}

.group-queue-list {
  max-height: 430px;
  overflow-y: auto;
}

.group-queue-item {
  cursor: grab;
  user-select: none;
  transition: background-color 0.16s ease, border-color 0.16s ease, opacity 0.16s ease;
}

.group-queue-item:active {
  cursor: grabbing;
}

.group-queue-item--dragging {
  opacity: 0.45;
}

.group-queue-item--drop-before {
  border-top: 2px solid rgba(13, 202, 240, 0.95) !important;
}

.group-queue-item--drop-after {
  border-bottom: 2px solid rgba(13, 202, 240, 0.95) !important;
}

.group-queue-handle {
  color: rgba(255, 255, 255, 0.42);
  font-size: 1rem;
  line-height: 1;
  letter-spacing: -0.08em;
  flex: 0 0 auto;
}

.group-queue-main {
  min-width: 0;
}

.scale-up {
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(25, 135, 84, 0.5);
  transition: all 0.2s ease-in-out;
}

.group-credit-card {
  min-width: 180px;
  padding: 0.85rem 1rem;
  border: 1px solid rgba(255, 193, 7, 0.35);
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.04);
}

.group-credit-count {
  min-width: 3.5rem;
}

.cups-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid #6c757d;
  color: white;
}
.cups-input:focus {
  background: rgba(0, 0, 0, 0.5);
  border-color: #0d6efd;
  color: white;
}

.match-team-btn {
  flex: 1 1 auto;
}

.match-team-name {
  display: inline-block;
  max-width: 150px;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-responsive {
  font-size: 0.875rem;
}
.table-success {
  background-color: rgba(25, 135, 84, 0.15) !important;
}
.table-hover tbody tr:hover {
  background-color: rgba(255, 255, 255, 0.075) !important;
}

@media (max-width: 768px) {
  .table-responsive {
    font-size: 0.8rem;
  }
  .cups-input {
    width: 50px !important;
  }
  .match-team-name {
    max-width: 100px;
    font-size: 0.8rem;
  }
}
</style>
