function safeNum(value) {
  const num = Number(value)
  return Number.isFinite(num) ? num : 0
}

function cloneMatch(match = {}) {
  const team1 = match.team1 ?? null
  const team2 = match.team2 ?? null
  const status = match.status ?? (match.winner ? 'done' : 'pending')
  const cupsTeam1 = safeNum(match.cups_team1)
  const cupsTeam2 = safeNum(match.cups_team2)
  let winner = match.winner === team1 || match.winner === team2 ? match.winner : null

  if (!winner && status === 'done' && team1 && team2 && cupsTeam1 !== cupsTeam2) {
    winner = cupsTeam1 > cupsTeam2 ? team1 : team2
  }

  return {
    id: match.id ?? null,
    team1,
    team2,
    winner,
    table_no: match.table_no ?? match.tableNo ?? null,
    status,
    cups_team1: cupsTeam1,
    cups_team2: cupsTeam2,
    cups_state_team1: Array.isArray(match.cups_state_team1) ? [...match.cups_state_team1] : null,
    cups_state_team2: Array.isArray(match.cups_state_team2) ? [...match.cups_state_team2] : null,
    rerack_used_team1: !!match.rerack_used_team1,
    rerack_used_team2: !!match.rerack_used_team2,
    is_overtime: !!match.is_overtime,
    label: match.label ?? match.match_label ?? null,
  }
}

function emptyMatch() {
  return {
    id: null,
    team1: null,
    team2: null,
    winner: null,
    table_no: null,
    cups_team1: 0,
    cups_team2: 0,
    cups_state_team1: null,
    cups_state_team2: null,
    rerack_used_team1: false,
    rerack_used_team2: false,
    is_overtime: false,
    status: 'pending',
    label: null,
  }
}

function buildEmptyRound(matchesCount) {
  return {
    bracket_type: 'main',
    round_name: '',
    matches: Array.from({ length: matchesCount }, emptyMatch),
  }
}

function buildPlacementRound() {
  return {
    bracket_type: 'placement',
    round_name: 'Spiel um Platz 3',
    matches: [emptyMatch()],
  }
}

function autoWinner(team1, team2) {
  if (team1 && !team2) return team1
  if (!team1 && team2) return team2
  return null
}

function roundNameFor(totalRounds, roundIdx) {
  const labels = ['Runde der 128', 'Runde der 64', 'Runde der 32', 'Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale']
  const base = Math.max(0, labels.length - totalRounds)
  return labels[base + roundIdx] || `Runde ${roundIdx + 1}`
}

function normalizeStoredRound(round = {}) {
  return {
    bracket_type: round.bracket_type || 'main',
    round_name: round.round_name || '',
    matches: (round.matches || []).map(cloneMatch),
  }
}

function propagateMainRounds(rounds) {
  for (let roundIdx = 0; roundIdx < rounds.length - 1; roundIdx++) {
    const current = rounds[roundIdx]
    const next = rounds[roundIdx + 1]
    if (!current || !next) continue
    if (current.bracket_type !== 'main' || next.bracket_type !== 'main') continue

    for (let matchIdx = 0; matchIdx < next.matches.length; matchIdx++) {
      const nextMatch = next.matches[matchIdx]
      const feederA = current.matches[matchIdx * 2]
      const feederB = current.matches[matchIdx * 2 + 1]

      const expectedTeam1 = feederA ? (feederA.winner || autoWinner(feederA.team1, feederA.team2)) : null
      const expectedTeam2 = feederB ? (feederB.winner || autoWinner(feederB.team1, feederB.team2)) : null

      nextMatch.team1 = expectedTeam1 || null
      nextMatch.team2 = expectedTeam2 || null
      nextMatch.table_no = null

      if (nextMatch.winner && nextMatch.winner !== nextMatch.team1 && nextMatch.winner !== nextMatch.team2) {
        nextMatch.winner = null
      }
    }
  }
}

function updatePlacementRound(rounds) {
  const placementIdx = rounds.findIndex(round => round.bracket_type === 'placement')
  if (placementIdx === -1) return

  const placement = rounds[placementIdx]
  const placementMatch = placement?.matches?.[0]
  if (!placementMatch) return

  const mainInfos = rounds
    .map((round, idx) => ({ round, idx }))
    .filter(entry => entry.round.bracket_type !== 'placement')

  if (mainInfos.length < 2) return

  const semiRound = rounds[mainInfos[mainInfos.length - 2].idx]
  const losers = []

  for (const match of semiRound.matches || []) {
    if (!match.team1 || !match.team2) continue
    const winner = match.winner || autoWinner(match.team1, match.team2)
    if (!winner) continue
    losers.push(winner === match.team1 ? match.team2 : match.team1)
  }

  placementMatch.team1 = losers[0] || null
  placementMatch.team2 = losers[1] || null
  placementMatch.table_no = null

  if (
    placementMatch.winner &&
    placementMatch.winner !== placementMatch.team1 &&
    placementMatch.winner !== placementMatch.team2
  ) {
    placementMatch.winner = null
  }
}

function isKoMatchInProgress(match = {}) {
  if (Number(match?.cups_team1) > 0 || Number(match?.cups_team2) > 0) return true
  if (match?.is_overtime) return true
  if (Array.isArray(match?.cups_state_team1) && match.cups_state_team1.some(c => c === false)) return true
  if (Array.isArray(match?.cups_state_team2) && match.cups_state_team2.some(c => c === false)) return true
  return false
}

export function getKoMainRoundInfos(rounds = []) {
  return (rounds || [])
    .map((round, idx) => ({ round, idx }))
    .filter(entry => (entry.round?.bracket_type || 'main') !== 'placement')
}

export function getKoPlacementRoundInfo(rounds = []) {
  return (rounds || [])
    .map((round, idx) => ({ round, idx }))
    .find(entry => (entry.round?.bracket_type || 'main') === 'placement') || null
}

export function isKoRoundComplete(round = {}) {
  const matches = round?.matches || []
  if (!matches.length) return false
  return matches.every(match => !match?.team1 || !match?.team2 || !!match?.winner)
}

function hasKoPlayableMatches(round = {}) {
  return (round?.matches || []).some(match => match?.team1 && match?.team2 && !match?.winner)
}

function hasKoRoundStarted(round = {}) {
  return (round?.matches || []).some(match =>
    (match?.team1 && match?.team2 && !!match?.winner) ||
    (match?.team1 && match?.team2 && isKoMatchInProgress(match))
  )
}

export function deriveKoActiveMainRoundIndex(rounds = [], explicitIndex = null) {
  const mainInfos = getKoMainRoundInfos(rounds)
  if (!mainInfos.length) return 0

  const parsedIndex = Number(explicitIndex)
  if (Number.isInteger(parsedIndex) && parsedIndex >= 0 && parsedIndex < mainInfos.length) {
    return parsedIndex
  }

  const inProgressIdx = mainInfos.findIndex(({ round }) =>
    (round?.matches || []).some(match =>
      match?.team1 && match?.team2 && !match?.winner && isKoMatchInProgress(match)
    )
  )
  if (inProgressIdx >= 0) return inProgressIdx

  const firstPendingIdx = mainInfos.findIndex(({ round }) =>
    (round?.matches || []).some(match => match?.team1 && match?.team2 && !match?.winner)
  )
  if (firstPendingIdx >= 0) return firstPendingIdx

  return Math.max(0, mainInfos.length - 1)
}

export function deriveKoActiveStageKind(rounds = [], explicitIndex = null, explicitStageKind = null) {
  const mainInfos = getKoMainRoundInfos(rounds)
  if (!mainInfos.length) return 'main'

  const activeMainRoundIndex = deriveKoActiveMainRoundIndex(rounds, explicitIndex)
  const placementInfo = getKoPlacementRoundInfo(rounds)
  if (!placementInfo || activeMainRoundIndex !== mainInfos.length - 1) return 'main'

  if (explicitStageKind === 'main' || explicitStageKind === 'placement') {
    return explicitStageKind
  }

  const finalInfo = mainInfos[activeMainRoundIndex]
  const placementStarted = hasKoRoundStarted(placementInfo?.round)
  const finalStarted = hasKoRoundStarted(finalInfo?.round)
  const placementPending = hasKoPlayableMatches(placementInfo?.round)
  const finalPending = hasKoPlayableMatches(finalInfo?.round)

  if (finalStarted) return 'main'
  if (placementStarted) return 'placement'
  if (placementPending && finalPending) return 'placement'
  if (placementPending && !finalPending) return 'placement'
  return 'main'
}

export function filterKoRoundsForActiveStage(rounds = [], explicitIndex = null, explicitStageKind = null) {
  const mainInfos = getKoMainRoundInfos(rounds)
  if (!mainInfos.length) return []

  const activeMainRoundIndex = deriveKoActiveMainRoundIndex(rounds, explicitIndex)
  const activeStageKind = deriveKoActiveStageKind(rounds, activeMainRoundIndex, explicitStageKind)
  const activeMainInfo = mainInfos[activeMainRoundIndex]
  const placementInfo = getKoPlacementRoundInfo(rounds)

  return (rounds || []).filter((round, idx) => {
    if ((round?.bracket_type || 'main') === 'placement') {
      return activeStageKind === 'placement' && idx === placementInfo?.idx
    }
    return activeStageKind === 'main' && idx === activeMainInfo?.idx
  })
}

export function getKoStageMeta(rounds = [], explicitIndex = null, explicitStageKind = null) {
  const mainInfos = getKoMainRoundInfos(rounds)
  if (!mainInfos.length) {
    return {
      activeMainRoundIndex: 0,
      activeStageKind: 'main',
      hasNextStage: false,
      currentRoundLabel: 'KO-Phase',
      nextRoundLabel: null,
      currentRoundComplete: false,
    }
  }

  const activeMainRoundIndex = deriveKoActiveMainRoundIndex(rounds, explicitIndex)
  const activeStageKind = deriveKoActiveStageKind(rounds, activeMainRoundIndex, explicitStageKind)
  const currentInfo = activeStageKind === 'placement'
    ? getKoPlacementRoundInfo(rounds)
    : mainInfos[activeMainRoundIndex]
  const nextInfo = mainInfos[activeMainRoundIndex + 1] || null
  const finalInfo = mainInfos[activeMainRoundIndex]
  const placementInfo = getKoPlacementRoundInfo(rounds)
  const currentRoundComplete = isKoRoundComplete(currentInfo?.round)

  let hasNextStage = false
  let nextRoundLabel = null

  if (activeStageKind === 'placement') {
    const finalAvailable = hasKoPlayableMatches(finalInfo?.round) || hasKoRoundStarted(finalInfo?.round)
    hasNextStage = finalAvailable
    nextRoundLabel = finalAvailable ? (finalInfo?.round?.round_name || 'Finale') : null
  } else if (nextInfo) {
    const placementAvailable = nextInfo === mainInfos[mainInfos.length - 1] && placementInfo && hasKoPlayableMatches(placementInfo.round)
    hasNextStage = true
    nextRoundLabel = placementAvailable
      ? (placementInfo?.round?.round_name || 'Spiel um Platz 3')
      : (nextInfo.round?.round_name || 'Nächste Runde')
  }

  return {
    activeMainRoundIndex,
    activeStageKind,
    hasNextStage,
    currentRoundLabel: currentInfo?.round?.round_name || 'KO-Phase',
    nextRoundLabel,
    currentRoundComplete,
  }
}

export function normalizeKoRoundsForDisplay(rawRounds = [], explicitKoSize = null) {
  const normalized = (rawRounds || []).map(normalizeStoredRound)
  if (!normalized.length) return []

  let mainRounds = normalized.filter(round => round.bracket_type !== 'placement')
  let placementRounds = normalized.filter(round => round.bracket_type === 'placement')

  if (!mainRounds.length) return placementRounds

  mainRounds = [...mainRounds].sort((a, b) => (b.matches?.length || 0) - (a.matches?.length || 0))

  const derivedSize = Math.max(2, (mainRounds[0]?.matches?.length || 1) * 2)
  const bracketSize = Math.max(2, Number(explicitKoSize) || 0, derivedSize)
  const totalRounds = Math.max(1, Math.floor(Math.log2(bracketSize)))

  while (mainRounds.length < totalRounds) {
    const prevLen = mainRounds[mainRounds.length - 1]?.matches?.length || 2
    mainRounds.push(buildEmptyRound(Math.max(1, prevLen >> 1)))
  }

  mainRounds = mainRounds.map((round, idx) => ({
    ...round,
    round_name: roundNameFor(totalRounds, idx),
  }))

  if (!placementRounds.length && bracketSize >= 4) {
    placementRounds = [buildPlacementRound()]
  }

  const rounds = [...mainRounds, ...placementRounds]
  propagateMainRounds(rounds)
  updatePlacementRound(rounds)

  return rounds
}
