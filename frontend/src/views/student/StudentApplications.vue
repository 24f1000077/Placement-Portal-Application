<template>
  <!-- Renders the student's applications list with search, filters, and a detail panel. -->
  <AppLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h4 mb-0">My Applications</h1>
      <button class="btn btn-outline-secondary" :disabled="exporting" @click="exportCsv">
        {{ exporting ? 'Preparing export…' : 'Export Placement History' }}
      </button>
    </div>

    <div v-if="exportMessage" class="alert alert-success py-2">{{ exportMessage }}</div>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control" style="max-width: 260px;" placeholder="Search company or drive…" />
      <MultiSelectDropdown label="Status" :options="STATUS_OPTIONS" v-model="statuses" />
      <span class="text-muted small ms-auto">{{ applications.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr><th>Company</th><th>Drive</th><th>Applied On</th><th>Status</th><th class="text-end">Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in applications" :key="a.id">
            <td>{{ a.company_name }}</td>
            <td>{{ a.job_title }}</td>
            <td>{{ formatDateTime(a.application_date) }}</td>
            <td><StatusBadge :status="a.status" /></td>
            <td class="text-end"><button class="btn btn-sm btn-outline-secondary" @click="openView(a)">View Details</button></td>
          </tr>
          <tr v-if="!applications.length"><td colspan="5" class="text-center text-muted py-4">No applications yet.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="viewOpen" title="Application Details" full-width>
      <div v-if="detail">
        <div class="row g-3 mb-4">
          <div class="col-md-4"><div class="text-muted small">Company</div><div class="fw-semibold">{{ detail.company_name }}</div></div>
          <div class="col-md-4"><div class="text-muted small">Drive</div><div class="fw-semibold">{{ detail.job_title }}</div></div>
          <div class="col-md-4"><div class="text-muted small">Applied On</div><div class="fw-semibold">{{ formatDateTime(detail.application_date) }}</div></div>
          <div class="col-md-3"><div class="text-muted small">Branch</div><div class="fw-semibold">{{ detail.student_branch || '—' }}</div></div>
          <div class="col-md-3"><div class="text-muted small">CGPA (at application)</div><div class="fw-semibold">{{ detail.student_cgpa }}</div></div>
          <div class="col-md-6">
            <div class="text-muted small">Resume (at application)</div>
            <button v-if="detail.has_resume" type="button" class="btn btn-sm btn-outline-secondary mt-1" @click="downloadFile(`/student/applications/${detail.id}/resume`, studentFileName(detail.student_name, 'resume.pdf'))">Download Resume</button>
            <div v-else class="fw-semibold">Not uploaded</div>
          </div>
          <div class="col-md-6"><div class="text-muted small">Skills (at application)</div><div class="fw-semibold">{{ detail.student_skills || '—' }}</div></div>
          <div class="col-md-6"><div class="text-muted small">Experience (at application)</div><div class="fw-semibold">{{ detail.student_experience || '—' }}</div></div>
        </div>

        <PipelineGraph :status="detail.status" :interviews="detail.interviews" :has-placement="!!detail.placement" />

        <div class="mt-4" v-if="detail.feedback">
          <div class="alert alert-secondary py-2 mb-0">{{ detail.feedback }}</div>
        </div>

        <div class="d-flex flex-wrap gap-2 mt-4">
          <button v-if="detail.interviews.length" class="btn btn-sm btn-outline-secondary" @click="interviewOpen = true">View Interview</button>
          <button v-if="['OFFER', 'PLACED'].includes(detail.status)" class="btn btn-sm btn-outline-secondary" @click="offerOpen = true">View Offer</button>
          <button v-if="detail.status === 'OFFER'" class="btn btn-sm btn-primary" @click="acceptOffer">Accept Offer</button>
          <button
            v-if="['APPLIED','SHORTLISTED','INTERVIEW','OFFER'].includes(detail.status)"
            class="btn btn-sm btn-outline-danger"
            @click="withdrawOpen = true"
          >Withdraw Application</button>
        </div>
      </div>
    </Modal>

    <Modal v-model="interviewOpen" title="Interview Details">
      <div v-if="detail">
        <div v-for="iv in detail.interviews" :key="iv.id" class="mb-3 pb-3 border-bottom">
          <div class="row g-2 small mb-2">
            <div class="col-6"><span class="text-muted">Scheduled:</span> {{ formatDateTime(iv.scheduled_date_time) }}</div>
            <div class="col-6"><span class="text-muted">Interviewer:</span> {{ iv.interviewer_name || '—' }}</div>
            <div class="col-6"><span class="text-muted">Status:</span> <StatusBadge :status="iv.status" /></div>
          </div>
          <div v-if="iv.notes" class="small mb-2"><span class="text-muted">Notes:</span> {{ iv.notes }}</div>
          <a v-if="iv.meeting_link" :href="iv.meeting_link" target="_blank" class="btn btn-sm btn-primary">Join Call</a>
        </div>
      </div>
    </Modal>

    <Modal v-model="offerOpen" title="Offer Details">
      <div v-if="detail">
        <div class="row g-2 small mb-3">
          <div class="col-6"><span class="text-muted">Offered Salary:</span> {{ detail.offered_salary }}</div>
          <div class="col-6"><span class="text-muted">Joining Date:</span> {{ formatDate(detail.offered_joining_date) }}</div>
        </div>
        <button v-if="detail.has_offer_letter" class="btn btn-sm btn-outline-secondary" @click="downloadFile(`/student/applications/${detail.id}/offer-letter`, studentFileName(detail.student_name, 'offer_letter.pdf'))">Download Offer Letter</button>
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
import { formatDate, formatDateTime } from '@/utils/date'
import { downloadFile, studentFileName } from '@/utils/download'
import { auth } from '@/utils/auth'

const STATUS_OPTIONS = ['APPLIED', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'PLACED', 'REJECTED', 'WITHDRAWN']

const applications = ref([])
const search = ref('')
const statuses = ref([])

const viewOpen = ref(false)
const interviewOpen = ref(false)
const offerOpen = ref(false)
const detail = ref(null)
const withdrawOpen = ref(false)
const exporting = ref(false)
const exportMessage = ref('')

// Fetches the applications list for the active search/filter state, newest first.
async function load() {
  const { data } = await api.get('/student/applications', {
    params: { search: search.value, status: statuses.value.join(',') },
  })
  applications.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([search, statuses], debouncedLoad, { deep: true })

onMounted(load)

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
  await load()
}

// Withdraws the active application.
async function withdraw() {
  const { data } = await api.post(`/student/applications/${detail.value.id}/withdraw`)
  detail.value = data
  await load()
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
    await downloadFile(`/student/applications/export/${taskId}/download`, studentFileName(auth.name, 'placement_history.csv'))
    exporting.value = false
    exportMessage.value = 'Your export is ready and the download has started.'
  }
  poll()
}
</script>
