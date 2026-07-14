<template>
  <!-- Renders a modal driven entirely by Vue state. -->
  <Teleport to="body">
    <div v-if="modelValue" class="modal d-block pp-modal-backdrop" tabindex="-1">
      <div class="modal-dialog modal-dialog-scrollable modal-dialog-centered" :class="fullWidth ? 'modal-xl' : 'modal-lg'">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ title }}</h5>
            <button type="button" class="btn-close" @click="close"></button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div class="modal-footer" v-if="$slots.footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  fullWidth: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

// Closes the modal by resetting the bound v-model flag.
function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.pp-modal-backdrop {
  background: rgba(15, 17, 31, 0.55);
}
</style>
