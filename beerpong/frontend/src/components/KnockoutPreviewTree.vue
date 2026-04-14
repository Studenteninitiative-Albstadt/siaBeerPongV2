<template>
  <TournamentBracketTree
    :slots="slots"
    :bracket-size="koSize"
    :show-third-place="true"
    :compact="true"
  />
</template>

<script setup>
import TournamentBracketTree from './TournamentBracketTree.vue'

defineProps({
  slots: { type: Array, default: () => [] },
  koSize: { type: Number, default: null },
})
</script>
