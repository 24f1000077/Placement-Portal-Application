<template>
  <!-- Renders the company's scheduled interviews with search and sort controls. -->
  <AppLayout>
    <h1 class="h4 mb-4">Interviews</h1>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <MultiSelectDropdown label="Drive" :options="driveOptions" v-model="driveIds" />
      <input v-model="studentName" type="search" class="form-control" style="max-width: 240px;" placeholder="Search candidate name…" />
      <select v-model="sort" class="form-select" style="max-width: 220px;" title="Sorts by the interview's scheduled date/time">
        <option value="newest">Latest scheduled first</option>
        <option value="oldest">Soonest scheduled first</option>
      </select>
      <span class="text-muted small ms-auto">{{ interviews.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr><th>Candidate</th><th>Drive</th><th>Scheduled</th><th>Interviewer</th><th>Notes</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="iv in interviews" :key="iv.id">
            <td>{{ iv.student_name }}</td>
            <td>{{ iv.job_title }}</td>
            <td>{{ formatDateTime(iv.scheduled_date_time) }}</td>
            <td>{{ iv.interviewer_name || '—' }}</td>
            <td>{{ iv.notes || '—' }}</td>
            <td><StatusBadge :status="iv.status" /></td>
          </tr>
          <tr v-if="!interviews.length"><td colspan="6" class="text-center text-muted py-4">No interviews scheduled.</td></tr>
        </tbody>
      </table>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDateTime } from '@/utils/date'

const interviews = ref([])
const driveOptions = ref([])
const driveIds = ref([])
const studentName = ref('')
const sort = ref('newest')

// Fetches the interview list for the active filter/sort state.
async function load() {
  const { data } = await api.get('/company/interviews', {
    params: { drive_ids: driveIds.value.join(','), student_name: studentName.value, sort: sort.value },
  })
  interviews.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([driveIds, studentName, sort], debouncedLoad, { deep: true })

onMounted(async () => {
  const { data } = await api.get('/company/drives')
  driveOptions.value = data.results.map((d) => ({ value: d.id, label: d.job_title }))
  await load()
})
</script>
