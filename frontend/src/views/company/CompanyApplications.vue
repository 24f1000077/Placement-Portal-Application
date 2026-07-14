<template>
  <!-- Renders the company applications workspace with pipeline actions. -->
  <AppLayout>
    <h1 class="h4 mb-4">Applications</h1>

    <div v-if="pinnedDriveLabel" class="alert alert-info py-2 d-flex align-items-center justify-content-between mb-3">
      <span>Showing applicants for <strong>{{ pinnedDriveLabel }}</strong></span>
      <button class="btn btn-sm btn-outline-secondary" @click="driveIds = []">Clear filter</button>
    </div>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control" style="max-width: 240px;" placeholder="Search student name…" />
      <MultiSelectDropdown label="Drive" :options="driveOptions" v-model="driveIds" />
      <MultiSelectDropdown label="Drive Status" :options="driveStatusOptions" v-model="driveStatuses" />
      <span class="text-muted small ms-auto">{{ applications.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr><th>Student</th><th>Drive</th><th>Applied On</th><th>Status</th><th class="text-end">Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="a in applications" :key="a.id">
            <td>{{ a.student_name }}</td>
            <td>{{ a.job_title }}</td>
            <td>{{ formatDateTime(a.application_date) }}</td>
            <td><StatusBadge :status="a.status" /></td>
            <td class="text-end"><button class="btn btn-sm btn-outline-secondary" @click="openView(a)">View</button></td>
          </tr>
          <tr v-if="!applications.length"><td colspan="5" class="text-center text-muted py-4">No applications found.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="viewOpen" title="Candidate Application" full-width>
      <div v-if="detail">
        <div class="row g-3 mb-4">
          <div class="col-md-3"><div class="text-muted small">Student</div><div class="fw-semibold">{{ detail.student_name }}</div></div>
          <div class="col-md-3"><div class="text-muted small">Branch</div><div class="fw-semibold">{{ detail.student_branch || '—' }}</div></div>
          <div class="col-md-2"><div class="text-muted small">CGPA (at application)</div><div class="fw-semibold">{{ detail.student_cgpa }}</div></div>
          <div class="col-md-4">
            <div class="text-muted small">Resume (at application)</div>
            <button v-if="detail.has_resume" class="btn btn-sm btn-outline-secondary mt-1" @click="downloadFile(`/company/applications/${detail.id}/resume`, studentFileName(detail.student_name, 'resume.pdf'))">Download Resume</button>
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
          <button v-if="detail.status === 'APPLIED'" class="btn btn-sm btn-primary" @click="setStatus('SHORTLISTED')">Shortlist</button>
          <button v-if="detail.status === 'SHORTLISTED'" class="btn btn-sm btn-primary" @click="scheduleOpen = true">Schedule Interview</button>
          <template v-if="detail.status === 'INTERVIEW'">
            <button class="btn btn-sm btn-outline-primary" @click="scheduleOpen = true">Schedule Interview</button>
            <button class="btn btn-sm btn-primary" @click="openOffer">Make an Offer</button>
          </template>
          <button v-if="['OFFER', 'PLACED'].includes(detail.status)" class="btn btn-sm btn-outline-secondary" @click="viewOfferOpen = true">View Offer</button>
          <button v-if="['APPLIED','SHORTLISTED','INTERVIEW','OFFER'].includes(detail.status)" class="btn btn-sm btn-outline-danger" @click="setStatus('REJECTED')">Reject</button>
        </div>

        <div class="mt-4" v-if="detail.interviews.length">
          <div class="text-muted small mb-2">Interviews</div>
          <table class="table pp-table table-sm mb-0">
            <thead>
              <tr><th>Scheduled</th><th>Interviewer</th><th>Notes</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="iv in detail.interviews" :key="iv.id">
                <td>{{ formatDateTime(iv.scheduled_date_time) }}</td>
                <td>{{ iv.interviewer_name }}</td>
                <td>{{ iv.notes || '—' }}</td>
                <td><StatusBadge :status="iv.status" /></td>
                <td><a v-if="iv.meeting_link" :href="iv.meeting_link" target="_blank" class="btn btn-sm btn-outline-primary">Join Call</a></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Modal>

    <Modal v-model="viewOfferOpen" title="Offer Details">
      <div v-if="detail">
        <div class="row g-2 small mb-3">
          <div class="col-6"><span class="text-muted">Offered Salary:</span> {{ detail.offered_salary }}</div>
          <div class="col-6"><span class="text-muted">Joining Date:</span> {{ formatDate(detail.offered_joining_date) }}</div>
        </div>
        <button v-if="detail.has_offer_letter" class="btn btn-sm btn-outline-secondary" @click="downloadFile(`/company/applications/${detail.id}/offer-letter`, studentFileName(detail.student_name, 'offer_letter.pdf'))">Download Offer Letter</button>
      </div>
    </Modal>

    <Modal v-model="scheduleOpen" title="Schedule Interview">
      <form @submit.prevent="submitSchedule" class="row g-3">
        <div class="col-12">
          <label class="form-label">Interviewer Name</label>
          <input v-model="scheduleForm.interviewer_name" class="form-control" required />
        </div>
        <div class="col-12">
          <label class="form-label">Date & Time</label>
          <input v-model="scheduleForm.scheduled_date_time" type="datetime-local" class="form-control" :min="minDateTimeLocal" required />
        </div>
        <div class="col-12">
          <label class="form-label">Meeting Link</label>
          <input v-model="scheduleForm.meeting_link" type="url" class="form-control" placeholder="https://" />
        </div>
        <div class="col-12">
          <label class="form-label">Notes</label>
          <textarea v-model="scheduleForm.notes" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary">Schedule</button>
        </div>
      </form>
    </Modal>

    <Modal v-model="offerOpen" title="Make an Offer">
      <form @submit.prevent="submitOffer" class="row g-3">
        <div class="col-12">
          <label class="form-label">Offered Salary</label>
          <input v-model.number="offerForm.salary_offered" type="number" min="0" step="0.01" class="form-control" required />
        </div>
        <div class="col-12">
          <label class="form-label">Projected Joining Date</label>
          <input v-model="offerForm.joining_date" type="date" class="form-control" :min="minDate" required />
        </div>
        <div class="col-12">
          <label class="form-label">Offer Letter (PDF)</label>
          <input type="file" accept="application/pdf" class="form-control" @change="onOfferFile" />
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary">Send Offer</button>
        </div>
      </form>
    </Modal>
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import PipelineGraph from '@/components/shared/PipelineGraph.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDate, formatDateTime, nowForDateTimeLocal, todayForDateInput } from '@/utils/date'
import { downloadFile, studentFileName } from '@/utils/download'

const route = useRoute()

const applications = ref([])
const driveOptions = ref([])
const driveStatusOptions = ref([])
const search = ref('')
const driveIds = ref([])
const driveStatuses = ref([])

// Shows which drive the list is currently pinned to, when arriving via a "View Applicants" link.
const pinnedDriveLabel = computed(() => {
  if (driveIds.value.length !== 1) return ''
  const match = driveOptions.value.find((d) => d.value === driveIds.value[0])
  return match ? match.label : ''
})

const viewOpen = ref(false)
const viewOfferOpen = ref(false)
const detail = ref(null)

const minDateTimeLocal = nowForDateTimeLocal()
const minDate = todayForDateInput()

const scheduleOpen = ref(false)
const scheduleForm = ref({ interviewer_name: '', scheduled_date_time: '', meeting_link: '', notes: '' })

const offerOpen = ref(false)
const offerForm = ref({ salary_offered: null, joining_date: '' })
let offerFile = null

// Fetches the company's applications for the active search/filter state.
async function load() {
  const { data } = await api.get('/company/applications', {
    params: {
      search: search.value,
      drive_ids: driveIds.value.join(','),
      drive_status: driveStatuses.value.join(','),
    },
  })
  applications.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([search, driveIds, driveStatuses], debouncedLoad, { deep: true })

onMounted(async () => {
  const { data } = await api.get('/company/drives')
  driveOptions.value = data.results.map((d) => ({ value: d.id, label: d.job_title }))
  // Builds the drive-status filter options from the company's own drives, fetched via the API
  // rather than hardcoded, so it always reflects the real PlacementDriveStatus values in use.
  driveStatusOptions.value = [...new Set(data.results.map((d) => d.status))]
  // Pre-apply a drive filter passed in via a "View Applicants" link from the Placement Drives page.
  if (route.query.drive_id) {
    driveIds.value = [Number(route.query.drive_id)]
  }
  await load()
})

// Opens the candidate detail/pipeline panel.
async function openView(application) {
  const { data } = await api.get(`/company/applications/${application.id}`)
  detail.value = data
  viewOpen.value = true
}

// Advances or rejects the candidate's pipeline status.
async function setStatus(status) {
  const { data } = await api.patch(`/company/applications/${detail.value.id}/status`, { status })
  detail.value = data
  await load()
}

// Submits the interview scheduling form.
async function submitSchedule() {
  await api.post(`/company/applications/${detail.value.id}/schedule-interview`, scheduleForm.value)
  scheduleOpen.value = false
  scheduleForm.value = { interviewer_name: '', scheduled_date_time: '', meeting_link: '', notes: '' }
  await openView({ id: detail.value.id })
}

// Opens the make-an-offer form with a blank state.
function openOffer() {
  offerForm.value = { salary_offered: null, joining_date: '' }
  offerFile = null
  offerOpen.value = true
}

// Captures the selected offer letter PDF file.
function onOfferFile(evt) {
  offerFile = evt.target.files[0] || null
}

// Submits the offer form, including the optional PDF upload.
async function submitOffer() {
  const payload = new FormData()
  payload.append('salary_offered', offerForm.value.salary_offered)
  payload.append('joining_date', offerForm.value.joining_date)
  if (offerFile) payload.append('offer_letter', offerFile)
  await api.post(`/company/applications/${detail.value.id}/offer`, payload, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  offerOpen.value = false
  await openView({ id: detail.value.id })
  await load()
}
</script>
