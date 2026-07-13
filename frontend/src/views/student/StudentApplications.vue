<template>
  <!-- Renders the student's applications, pipeline detail panel, and placement history. -->
  <AppLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h4 mb-0">My Applications</h1>
      <button class="btn btn-outline-secondary" :disabled="exporting" @click="exportCsv">
        {{ exporting ? 'Preparing export…' : 'Export to CSV' }}
      </button>
    </div>

    <div v-if="exportMessage" class="alert alert-success py-2">{{ exportMessage }}</div>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <MultiSelectDropdown label="Status" :options="STATUS_OPTIONS" v-model="statuses" />
      <span class="text-muted small ms-auto">{{ applications.length }} record(s)</span>
    </div>

    <div class="pp-card mb-4">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr><th>Company</th><th>Drive</th><th>Applied On</th><th>Status</th><th class="text-end">Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in applications" :key="a.id">
            <td>{{ a.company_name }}</td>
            <td>{{ a.job_title }}</td>
            <td>{{ formatDate(a.application_date) }}</td>
            <td><StatusBadge :status="a.status" /></td>
            <td class="text-end"><button class="btn btn-sm btn-outline-secondary" @click="openView(a)">View Details</button></td>
          </tr>
          <tr v-if="!applications.length"><td colspan="5" class="text-center text-muted py-4">No applications yet.</td></tr>
        </tbody>
      </table>
    </div>

    <h2 class="h6 text-muted mb-3">Placement History</h2>
    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr><th>Student ID</th><th>Company</th><th>Drive</th><th>Status</th><th>Date</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in history" :key="a.id">
            <td>{{ a.student_id }}</td>
            <td>{{ a.company_name }}</td>
            <td>{{ a.job_title }}</td>
            <td><StatusBadge :status="a.status" /></td>
            <td>{{ formatDate(a.application_date) }}</td>
          </tr>
          <tr v-if="!history.length"><td colspan="5" class="text-center text-muted py-4">No historical records yet.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="viewOpen" title="Application Details" full-width>
      <div v-if="detail">
        <div class="row g-3 mb-4">
          <div class="col-md-4"><div class="text-muted small">Company</div><div class="fw-semibold">{{ detail.company_name }}</div></div>
          <div class="col-md-4"><div class="text-muted small">Drive</div><div class="fw-semibold">{{ detail.job_title }}</div></div>
          <div class="col-md-4"><div class="text-muted small">Applied On</div><div class="fw-semibold">{{ formatDate(detail.application_date) }}</div></div>
        </div>

        <PipelineGraph :status="detail.status" :interviews="detail.interviews" :has-placement="!!detail.placement" />

        <div class="mt-4" v-if="detail.interviews.length">
          <div class="text-muted small mb-2">Interview Schedule</div>
          <ul class="list-unstyled mb-0">
            <li v-for="iv in detail.interviews" :key="iv.id">
              {{ formatDate(iv.scheduled_date_time) }} — {{ iv.interviewer_name }}
              <a v-if="iv.meeting_link" :href="iv.meeting_link" target="_blank" class="ms-1">Join link</a>
            </li>
          </ul>
        </div>

        <div class="mt-4" v-if="detail.feedback">
          <div class="text-muted small mb-1">Feedback</div>
          <p class="mb-0">{{ detail.feedback }}</p>
        </div>

        <div class="d-flex flex-wrap gap-2 mt-4">
          <template v-if="detail.status === 'OFFER'">
            <button class="btn btn-sm btn-primary" @click="acceptOffer">Accept Offer</button>
            <button class="btn btn-sm btn-outline-danger" @click="rejectOffer">Reject Offer</button>
          </template>
          <button
            v-if="['APPLIED','SHORTLISTED','INTERVIEW','OFFER'].includes(detail.status)"
            class="btn btn-sm btn-outline-secondary"
            @click="withdrawOpen = true"
          >Withdraw Application</button>
        </div>
      </div>
    </Modal>

    <ConfirmDialog
      v-model="withdrawOpen"
      title="Withdraw Application"
      message="This withdraws your application and you will not be able to re-apply to this drive. Continue?"
      confirm-label="Withdraw"
      @confirm="withdraw"
    />
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import PipelineGraph from '@/components/shared/PipelineGraph.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'

const STATUS_OPTIONS = ['APPLIED', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'PLACED', 'REJECTED', 'WITHDRAWN']

const applications = ref([])
const history = ref([])
const statuses = ref([])

const viewOpen = ref(false)
const detail = ref(null)
const withdrawOpen = ref(false)
const exporting = ref(false)
const exportMessage = ref('')

// Formats an ISO date string for display.
function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString() : '—'
}

// Fetches the filtered applications list.
async function load() {
  const { data } = await api.get('/student/applications', { params: { status: statuses.value.join(',') } })
  applications.value = data.results
}

// Fetches the full unfiltered historical record.
async function loadHistory() {
  const { data } = await api.get('/student/applications')
  history.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch(statuses, debouncedLoad, { deep: true })

onMounted(async () => {
  await Promise.all([load(), loadHistory()])
})

// Opens the detail/pipeline panel for an application.
async function openView(application) {
  const { data } = await api.get(`/student/applications/${application.id}`)
  detail.value = data
  viewOpen.value = true
}

// Accepts the current offer, finalizing the placement.
async function acceptOffer() {
  const { data } = await api.post(`/student/applications/${detail.value.id}/accept-offer`)
  detail.value = data
  await Promise.all([load(), loadHistory()])
}

// Rejects the current offer, freeing the slot.
async function rejectOffer() {
  const { data } = await api.post(`/student/applications/${detail.value.id}/reject-offer`)
  detail.value = data
  await Promise.all([load(), loadHistory()])
}

// Withdraws the active application.
async function withdraw() {
  const { data } = await api.post(`/student/applications/${detail.value.id}/withdraw`)
  detail.value = data
  await Promise.all([load(), loadHistory()])
}

// Triggers the async CSV export and polls until it's ready, then downloads it.
async function exportCsv() {
  exporting.value = true
  exportMessage.value = ''
  const { data } = await api.post('/student/applications/export')
  const taskId = data.task_id
  const poll = async () => {
    const { data: status } = await api.get(`/student/applications/export/${taskId}`)
    if (!status.ready) {
      setTimeout(poll, 1500)
      return
    }
    const res = await api.get(`/student/applications/export/${taskId}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = 'applications.csv'
    link.click()
    URL.revokeObjectURL(url)
    exporting.value = false
    exportMessage.value = 'Your export is ready and the download has started.'
  }
  poll()
}
</script>
