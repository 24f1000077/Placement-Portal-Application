<template>
  <!-- Renders the campus-wide interview log with search and sort controls. -->
  <AppLayout>
    <h1 class="h4 mb-4">Interviews</h1>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="driveOrCompany" type="search" class="form-control" style="max-width: 240px;" placeholder="Search drive or company…" />
      <input v-model="studentName" type="search" class="form-control" style="max-width: 240px;" placeholder="Search student name…" />
      <select v-model="sort" class="form-select" style="max-width: 200px;">
        <option value="newest">Newest first</option>
        <option value="oldest">Oldest first</option>
      </select>
      <span class="text-muted small ms-auto">{{ interviews.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr>
            <th>Student</th>
            <th>Drive</th>
            <th>Company</th>
            <th>Scheduled</th>
            <th>Interviewer</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="iv in interviews" :key="iv.id">
            <td>{{ iv.student_name }}</td>
            <td>{{ iv.job_title }}</td>
            <td>{{ iv.company_name }}</td>
            <td>{{ formatDate(iv.scheduled_date_time) }}</td>
            <td>{{ iv.interviewer_name || '—' }}</td>
            <td><StatusBadge :status="iv.status" /></td>
          </tr>
          <tr v-if="!interviews.length"><td colspan="6" class="text-center text-muted py-4">No interviews found.</td></tr>
        </tbody>
      </table>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'

const interviews = ref([])
const driveOrCompany = ref('')
const studentName = ref('')
const sort = ref('newest')

// Formats an ISO date string for display.
function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString() : '—'
}

// Fetches the interview log for the active search/sort state.
async function load() {
  const { data } = await api.get('/admin/interviews', {
    params: { search_drive_company: driveOrCompany.value, student_name: studentName.value, sort: sort.value },
  })
  interviews.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([driveOrCompany, studentName, sort], debouncedLoad)
onMounted(load)
</script>
