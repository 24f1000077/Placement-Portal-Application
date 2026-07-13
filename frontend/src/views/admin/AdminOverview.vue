<template>
  <!-- Renders the admin landing page with the three summary metric cards. -->
  <AppLayout>
    <h1 class="h4 mb-4">Overview</h1>
    <div class="row g-3">
      <div class="col-md-4">
        <div class="pp-card p-4">
          <div class="text-muted small">Total Students</div>
          <div class="display-6 fw-bold">{{ metrics.total_students ?? '—' }}</div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="pp-card p-4">
          <div class="text-muted small">Approved Companies</div>
          <div class="display-6 fw-bold">{{ metrics.total_companies_approved ?? '—' }}</div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="pp-card p-4">
          <div class="text-muted small">Approved Placement Drives</div>
          <div class="display-6 fw-bold">{{ metrics.total_drives_approved ?? '—' }}</div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import api from '@/services/api'

const metrics = reactive({})

// Loads the admin summary metrics.
onMounted(async () => {
  const { data } = await api.get('/admin/overview')
  Object.assign(metrics, data)
})
</script>
