<template>
  <!-- Renders the company landing page with profile summary and drive applicant counts. -->
  <AppLayout>
    <h1 class="h4 mb-4">Overview</h1>

    <div class="pp-card p-4 mb-4" v-if="profile">
      <div class="row g-3">
        <div class="col-md-3"><div class="text-muted small">Company Name</div><div class="fw-semibold">{{ profile.company_name }}</div></div>
        <div class="col-md-3"><div class="text-muted small">HR Contact</div><div class="fw-semibold">{{ profile.email }}</div></div>
        <div class="col-md-3"><div class="text-muted small">Website</div><div class="fw-semibold">{{ profile.website || '—' }}</div></div>
        <div class="col-md-3"><div class="text-muted small">Industry</div><div class="fw-semibold">{{ profile.industry || '—' }}</div></div>
      </div>
    </div>

    <h2 class="h6 text-muted mb-3">My Placement Drives</h2>
    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr><th>Job Title</th><th>Status</th><th>Deadline</th><th>Applicants</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in drives" :key="d.id">
            <td>{{ d.job_title }}</td>
            <td><StatusBadge :status="d.status" /></td>
            <td>{{ d.application_deadline ? new Date(d.application_deadline).toLocaleDateString() : '—' }}</td>
            <td>{{ d.applicant_count }}</td>
          </tr>
          <tr v-if="!drives.length"><td colspan="4" class="text-center text-muted py-4">No placement drives yet.</td></tr>
        </tbody>
      </table>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import api from '@/services/api'

const profile = ref(null)
const drives = ref([])

// Loads the company profile summary and drive list.
onMounted(async () => {
  const { data } = await api.get('/company/overview')
  profile.value = data.profile
  drives.value = data.drives
})
</script>
