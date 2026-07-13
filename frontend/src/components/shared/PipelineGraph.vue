<template>
  <!-- Renders the 5-stage application pipeline, highlighting rejection/withdrawal in red. -->
  <div class="d-flex align-items-center pp-pipeline">
    <template v-for="(stage, i) in STAGES" :key="stage">
      <div class="d-flex flex-column align-items-center pp-pipeline-node">
        <div class="pp-pipeline-dot" :class="dotClass(i)"></div>
        <div class="pp-pipeline-label" :class="{ 'text-danger fw-semibold': isTerminal && i === reachedIndex }">
          {{ i === reachedIndex && isTerminal ? status : stage }}
        </div>
      </div>
      <div v-if="i < STAGES.length - 1" class="pp-pipeline-line" :class="{ 'pp-pipeline-line-done': i < reachedIndex }"></div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const STAGES = ['APPLIED', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'PLACED']

const props = defineProps({
  status: { type: String, required: true },
  interviews: { type: Array, default: () => [] },
  hasPlacement: { type: Boolean, default: false },
})

const isTerminal = computed(() => props.status === 'REJECTED' || props.status === 'WITHDRAWN')

// Resolves the furthest pipeline stage the application reached.
const reachedIndex = computed(() => {
  if (!isTerminal.value) return STAGES.indexOf(props.status)
  if (props.hasPlacement) return 4
  if (props.interviews.length) return 2
  return 0
})

// Resolves the dot color class for a given stage index.
function dotClass(i) {
  if (isTerminal.value && i === reachedIndex.value) return 'pp-dot-rejected'
  if (i < reachedIndex.value) return 'pp-dot-done'
  if (i === reachedIndex.value) return 'pp-dot-active'
  return 'pp-dot-pending'
}
</script>

<style scoped>
.pp-pipeline {
  overflow-x: auto;
  padding: 0.5rem 0;
}
.pp-pipeline-node {
  min-width: 92px;
}
.pp-pipeline-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  margin-bottom: 0.4rem;
}
.pp-dot-done { background: var(--pp-status-approved); }
.pp-dot-active { background: var(--pp-primary); box-shadow: 0 0 0 4px rgba(47, 63, 168, 0.15); }
.pp-dot-pending { background: var(--pp-border); }
.pp-dot-rejected { background: var(--pp-status-rejected); box-shadow: 0 0 0 4px rgba(179, 38, 30, 0.15); }
.pp-pipeline-label {
  font-size: 0.75rem;
  color: var(--pp-text-muted);
  text-align: center;
}
.pp-pipeline-line {
  flex: 1;
  height: 2px;
  background: var(--pp-border);
  min-width: 24px;
  margin-bottom: 1.3rem;
}
.pp-pipeline-line-done {
  background: var(--pp-status-approved);
}
</style>
