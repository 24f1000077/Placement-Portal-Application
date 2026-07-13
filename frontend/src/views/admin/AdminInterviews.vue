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
            <th>Notes</th>
            <th>Status</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="iv in interviews" :key="iv.id">
            <td>{{ iv.student_name }}</td>
            <td>{{ iv.job_title }}</td>
            <td>{{ iv.company_name }}</td>
            <td>{{ formatDateTime(iv.scheduled_date_time) }}</td>
            <td>{{ iv.interviewer_name || '—' }}</td>
            <td>{{ iv.notes || '—' }}</td>
            <td><StatusBadge :status="iv.status" /></td>
            <td class="text-end"><button class="btn btn-sm btn-outline-secondary" @click="openEdit(iv)">Edit</button></td>
          </tr>
          <tr v-if="!interviews.length"><td colspan="8" class="text-center text-muted py-4">No interviews found.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="editOpen" title="Edit Interview">
      <form v-if="editing" class="row g-3" @submit.prevent="saveEdit">
        <div class="col-md-6">
          <label class="form-label">Interviewer Name</label>
          <input v-model="editing.interviewer_name" class="form-control" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Date &amp; Time</label>
          <input v-model="editing.scheduled_date_time" type="datetime-local" class="form-control" required />
        </div>
        <div class="col-12">
          <label class="form-label">Meeting Link</label>
          <input v-model="editing.meeting_link" type="url" class="form-control" placeholder="https://" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Status</label>
          <select v-model="editing.status" class="form-select">
            <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="col-12">
          <label class="form-label">Notes</label>
          <textarea v-model="editing.notes" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12">
          <label class="form-label">Feedback</label>
          <textarea v-model="editing.feedback" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
        </div>
      </form>
    </Modal>
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDateTime } from '@/utils/date'

const STATUS_OPTIONS = ['SCHEDULED', 'COMPLETED', 'CANCELLED']

const interviews = ref([])
const driveOrCompany = ref('')
const studentName = ref('')
const sort = ref('newest')

const editOpen = ref(false)
const editing = ref(null)
const saving = ref(false)

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

// Opens the edit modal for a given interview.
function openEdit(interview) {
  editing.value = {
    ...interview,
    scheduled_date_time: interview.scheduled_date_time ? interview.scheduled_date_time.slice(0, 16) : '',
  }
  editOpen.value = true
}

// Saves the edited interview fields.
async function saveEdit() {
  saving.value = true
  try {
    await api.patch(`/admin/interviews/${editing.value.id}`, {
      interviewer_name: editing.value.interviewer_name,
      scheduled_date_time: editing.value.scheduled_date_time,
      meeting_link: editing.value.meeting_link,
      status: editing.value.status,
      notes: editing.value.notes,
      feedback: editing.value.feedback,
    })
    editOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}
</script>
