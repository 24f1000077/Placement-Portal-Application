<template>
  <!-- Renders a confirmation prompt for a destructive or access-changing action. -->
  <Modal v-model="proxyOpen" :title="title">
    <p class="mb-0">{{ message }}</p>
    <template #footer>
      <button type="button" class="btn btn-outline-secondary" @click="proxyOpen = false">Cancel</button>
      <button type="button" class="btn btn-primary" @click="onConfirm">{{ confirmLabel }}</button>
    </template>
  </Modal>
</template>

<script setup>
import { computed } from 'vue'
import Modal from '@/components/shared/Modal.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: 'Please Confirm' },
  message: { type: String, default: 'Are you sure?' },
  confirmLabel: { type: String, default: 'Confirm' },
})
const emit = defineEmits(['update:modelValue', 'confirm'])

const proxyOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

// Emits the confirm event and closes the dialog.
function onConfirm() {
  emit('confirm')
  proxyOpen.value = false
}
</script>
