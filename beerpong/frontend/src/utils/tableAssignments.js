export function matchKey(match) {
  if (match?.id !== undefined && match?.id !== null) return `id:${match.id}`
  return `fallback:${match?.group_name || ''}:${match?.team1 || ''}:${match?.team2 || ''}:${match?.order_index ?? 0}`
}

export function getTableNo(match) {
  const raw = Number(
    match?.table_no ??
    match?.tableNo ??
    match?.table_number ??
    match?.tableNumber ??
    null
  )
  return Number.isFinite(raw) && raw > 0 ? raw : null
}

export function flattenMatchesByGroup(matchesByGroup = {}) {
  const all = []
  for (const [groupName, matches] of Object.entries(matchesByGroup || {})) {
    for (let i = 0; i < (matches || []).length; i++) {
      all.push({
        ...matches[i],
        group_name: matches[i]?.group_name ?? groupName,
        originalIndex: i,
      })
    }
  }
  all.sort((a, b) => {
    const orderDiff = Number(a.order_index ?? 0) - Number(b.order_index ?? 0)
    if (orderDiff !== 0) return orderDiff
    return String(a.group_name || '').localeCompare(String(b.group_name || ''), 'de')
  })
  return all
}

/**
 * Returns true if a match is actively in progress (cups hit, history, or overtime).
 * Used to stabilize table assignments for matches that are physically being played
 * even when their table_no hasn't been persisted to the backend yet.
 */
export function isMatchInProgress(match) {
  if (Number(match?.cups_team1) > 0 || Number(match?.cups_team2) > 0) return true
  if (match?.is_overtime) return true
  if (Array.isArray(match?.cups_state_team1) && match.cups_state_team1.some(c => c === false)) return true
  if (Array.isArray(match?.cups_state_team2) && match.cups_state_team2.some(c => c === false)) return true
  if (Array.isArray(match?.history_team1) && match.history_team1.length > 0) return true
  if (Array.isArray(match?.history_team2) && match.history_team2.length > 0) return true
  return false
}

export function buildStableTableAssignmentMap(matchesByGroup = {}, tableCount = 0) {
  const maxTables = Math.max(0, Number(tableCount) || 0)
  const flat = flattenMatchesByGroup(matchesByGroup)
  const pending = flat.filter(match => !match.winner)
  const assignedByTable = new Map()
  const occupiedTeams = new Set()

  // Pass 1: Honor explicitly persisted table_no assignments (matches already saved to backend)
  for (const match of pending) {
    const tableNo = getTableNo(match)
    if (!tableNo || tableNo > maxTables) continue
    if (assignedByTable.has(tableNo)) continue
    if (occupiedTeams.has(match.team1) || occupiedTeams.has(match.team2)) continue
    assignedByTable.set(tableNo, match)
    occupiedTeams.add(match.team1)
    occupiedTeams.add(match.team2)
  }

  // Pass 2: In-progress matches without a persisted table_no are physically at a table.
  // Assign them to the lowest available slot to keep them stable and prevent
  // waiting-queue matches from jumping ahead of them.
  const inProgressOrphans = pending.filter(m => !getTableNo(m) && isMatchInProgress(m))
  for (const match of inProgressOrphans) {
    if (occupiedTeams.has(match.team1) || occupiedTeams.has(match.team2)) continue
    for (let tableNo = 1; tableNo <= maxTables; tableNo++) {
      if (!assignedByTable.has(tableNo)) {
        assignedByTable.set(tableNo, match)
        occupiedTeams.add(match.team1)
        occupiedTeams.add(match.team2)
        break
      }
    }
  }

  // Collect all remaining unassigned pending matches (the waiting queue)
  const assignedKeys = new Set([...assignedByTable.values()].map(m => matchKey(m)))
  const unassigned = pending.filter(m => !assignedKeys.has(matchKey(m)))

  // Pass 3: Fill empty tables from the queue. Each empty table gets the next eligible
  // match where neither team is already playing at another table.
  // Tables are filled in order (1, 2, 3…) so lower table numbers get priority.
  // A match at Table 2 will NEVER migrate to Table 1 — once assigned (Pass 1/2) it stays.
  for (let tableNo = 1; tableNo <= maxTables; tableNo++) {
    if (assignedByTable.has(tableNo)) continue
    const candidateIndex = unassigned.findIndex(match =>
      !occupiedTeams.has(match.team1) && !occupiedTeams.has(match.team2)
    )
    if (candidateIndex === -1) continue
    const [candidate] = unassigned.splice(candidateIndex, 1)
    assignedByTable.set(tableNo, candidate)
    occupiedTeams.add(candidate.team1)
    occupiedTeams.add(candidate.team2)
  }

  const assignmentMap = new Map()
  for (const [tableNo, match] of assignedByTable.entries()) {
    assignmentMap.set(matchKey(match), tableNo)
  }
  return assignmentMap
}

export function getAssignedActiveMatches(matchesByGroup = {}, tableCount = 0) {
  const assignments = buildStableTableAssignmentMap(matchesByGroup, tableCount)
  return flattenMatchesByGroup(matchesByGroup)
    .filter(match => !match.winner)
    .map(match => {
      const assignedTable = assignments.get(matchKey(match))
      return assignedTable ? { ...match, table_no: assignedTable } : match
    })
    .filter(match => !!getTableNo(match))
    .sort((a, b) => getTableNo(a) - getTableNo(b))
}

export function getUpcomingMatches(matchesByGroup = {}, tableCount = 0, limit = 10) {
  const activeMatches = getAssignedActiveMatches(matchesByGroup, tableCount)
  const activeKeys = new Set(activeMatches.map(match => matchKey(match)))

  return flattenMatchesByGroup(matchesByGroup)
    .filter(match => !match.winner && !activeKeys.has(matchKey(match)))
    .slice(0, limit)
}

// ── KO phase utilities ────────────────────────────────────────────────────────

export function flattenKORounds(rounds = []) {
  const all = []
  for (const round of (rounds || [])) {
    for (let i = 0; i < (round.matches || []).length; i++) {
      all.push({
        ...round.matches[i],
        round_name: round.round_name,
        bracket_type: round.bracket_type,
        ko_match_index: i,
      })
    }
  }
  return all
}

export function getKOActiveMatches(rounds = [], tableCount = 0) {
  const maxTables = Math.max(0, Number(tableCount) || 0)
  if (maxTables === 0) return []
  const pending = flattenKORounds(rounds).filter(m => !m.winner && m.team1 && m.team2)
  return pending.slice(0, maxTables).map((m, i) => ({ ...m, table_no: i + 1 }))
}

export function getKOUpcomingMatches(rounds = [], tableCount = 0, limit = 10) {
  const active = getKOActiveMatches(rounds, tableCount)
  const activeIds = new Set(active.map(m => m.id).filter(id => id != null))
  return flattenKORounds(rounds)
    .filter(m => !m.winner && m.team1 && m.team2 && !activeIds.has(m.id))
    .slice(0, limit)
}

export function makeCupsStateFromCount(hitCount, totalCups = 6) {
  const state = Array(totalCups).fill(true)
  const hits = Math.min(Math.max(0, hitCount || 0), totalCups)
  for (let i = totalCups - 1; i >= totalCups - hits; i--) state[i] = false
  return state
}
