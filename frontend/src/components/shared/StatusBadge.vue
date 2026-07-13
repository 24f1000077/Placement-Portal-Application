<template>
  <!-- Renders a color-coded pill for the given status value. -->
  <span class="pp-badge" :class="badgeClass">{{ status }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: { type: String, required: true } })

const MAP = {
  PENDING: 'pp-badge-pending',
  APPROVED: 'pp-badge-approved',
  PLACED: 'pp-badge-approved',
  OFFER: 'pp-badge-approved',
  REJECTED: 'pp-badge-rejected',
  WITHDRAWN: 'pp-badge-rejected',
  BLACKLISTED: 'pp-badge-blacklisted',
  CLOSED: 'pp-badge-closed',
  CANCELLED: 'pp-badge-cancelled',
}

// Resolves the badge color class for the current status.
const badgeClass = computed(() => MAP[props.status] || 'pp-badge-closed')
</script>
