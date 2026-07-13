<template>
  <!-- Wraps every protected dashboard page with the shared header bar. -->
  <div class="pp-shell">
    <HeaderBar />
    <main class="container-fluid pp-content px-3 px-md-4 py-4">
      <slot />
    </main>
  </div>
</template>

<script setup>
import HeaderBar from '@/components/shared/HeaderBar.vue'
</script>

<style scoped>
.pp-shell {
  min-height: 100vh;
}
.pp-content {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
