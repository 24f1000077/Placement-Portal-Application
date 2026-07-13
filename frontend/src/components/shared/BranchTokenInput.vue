<template>
  <!-- Renders eligible branches as removable token pills with a matching text input. -->
  <div>
    <div class="d-flex flex-wrap gap-2 mb-2" v-if="selected.length">
      <span v-for="b in selected" :key="b.id" class="pp-token">
        {{ b.name }}
        <button type="button" class="pp-token-remove" @click="remove(b.id)">×</button>
      </span>
    </div>
    <input
      list="branch-options"
      class="form-control"
      placeholder="Type a branch name and press Enter"
      v-model="draft"
      @keydown.enter.prevent="tryAdd"
      @change="tryAdd"
    />
    <datalist id="branch-options">
      <option v-for="b in available" :key="b.id" :value="b.name" />
    </datalist>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: Array, required: true },
  options: { type: Array, required: true },
})
const emit = defineEmits(['update:modelValue'])

const draft = ref('')

// Resolves the full branch objects for the currently selected ids.
const selected = computed(() => props.options.filter((b) => props.modelValue.includes(b.id)))
// Resolves branches not yet selected, for the suggestion list.
const available = computed(() => props.options.filter((b) => !props.modelValue.includes(b.id)))

// Converts a matching typed branch name into a locked pill.
function tryAdd() {
  const match = props.options.find((b) => b.name.toLowerCase() === draft.value.trim().toLowerCase())
  if (match && !props.modelValue.includes(match.id)) {
    emit('update:modelValue', [...props.modelValue, match.id])
  }
  draft.value = ''
}

// Removes a branch pill from the selection.
function remove(id) {
  emit('update:modelValue', props.modelValue.filter((v) => v !== id))
}
</script>

<style scoped>
.pp-token {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--pp-status-approved-bg);
  color: var(--pp-status-approved);
  border-radius: 999px;
  padding: 0.25rem 0.5rem 0.25rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
}
.pp-token-remove {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.2rem;
}
</style>
