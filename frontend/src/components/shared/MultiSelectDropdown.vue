<template>
  <!-- Renders a checkbox-based multi-select filter dropdown. -->
  <div class="dropdown">
    <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" data-bs-auto-close="outside">
      {{ label }}<span v-if="modelValue.length" class="badge text-bg-secondary ms-1">{{ modelValue.length }}</span>
    </button>
    <ul class="dropdown-menu p-2 pp-dropdown-menu">
      <li v-for="opt in options" :key="optionValue(opt)" class="form-check px-2">
        <input
          class="form-check-input"
          type="checkbox"
          :id="`opt-${label}-${optionValue(opt)}`"
          :checked="modelValue.includes(optionValue(opt))"
          @change="toggle(optionValue(opt))"
        />
        <label class="form-check-label" :for="`opt-${label}-${optionValue(opt)}`">{{ optionLabel(opt) }}</label>
      </li>
    </ul>
  </div>
</template>

<script setup>
const props = defineProps({
  label: { type: String, required: true },
  options: { type: Array, required: true },
  modelValue: { type: Array, required: true },
})
const emit = defineEmits(['update:modelValue'])

// Resolves the underlying value for a string or {value,label} option.
function optionValue(opt) {
  return typeof opt === 'string' ? opt : opt.value
}
// Resolves the display label for a string or {value,label} option.
function optionLabel(opt) {
  return typeof opt === 'string' ? opt : opt.label
}

// Adds or removes a value from the selected set.
function toggle(value) {
  const next = props.modelValue.includes(value)
    ? props.modelValue.filter((v) => v !== value)
    : [...props.modelValue, value]
  emit('update:modelValue', next)
}
</script>

<style scoped>
.pp-dropdown-menu {
  min-width: 220px;
  max-height: 260px;
  overflow-y: auto;
}
</style>
