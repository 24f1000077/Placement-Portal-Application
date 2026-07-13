<template>
  <!-- Renders the admin applications table with a single unified read-only view panel. -->
  <AppLayout>
    <h1 class="h4 mb-4">Applications</h1>

    <div v-if="pinnedFilterLabel" class="alert alert-info py-2 d-flex align-items-center justify-content-between mb-3">
      <span>Showing applications for <strong>{{ pinnedFilterLabel }}</strong></span>
      <button class="btn btn-sm btn-outline-secondary" @click="companyIds = []; driveIds = []">Clear filter</button>
    </div>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control" style="max-width: 240px;" placeholder="Search student name…" />
      <MultiSelectDropdown label="Company" :options="companyOptions" v-model="companyIds" />
      <MultiSelectDropdown label="Drive" :options="driveOptions" v-model="driveIds" />
      <MultiSelectDropdown label="Status" :options="STATUS_OPTIONS" v-model="statuses" />
      <span class="text-muted small ms-auto">{{ applications.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr>
            <th>Student</th>
            <th>Company</th>
            <th>Drive</th>
            <th>Applied On</th>
            <th>Status</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in applications" :key="a.id">
            <td>{{ a.student_name }}</td>
            <td>{{ a.company_name }}</td>
            <td>{{ a.job_title }}</td>
            <td>{{ formatDateTime(a.application_date) }}</td>
            <td><StatusBadge :status="a.status" /></td>
            <td class="text-end"><button class="btn btn-sm btn-outline-secondary" @click="openView(a)">View</button></td>
          </tr>
          <tr v-if="!applications.length"><td colspan="6" class="text-center text-muted py-4">No applications found.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="viewOpen" title="Application Details" full-width>
      <form v-if="detail" @submit.prevent="saveApplication">
        <div class="row g-3 mb-4">
          <div class="col-md-3"><div class="text-muted small">Student</div><div class="fw-semibold">{{ detail.student_name }}</div></div>
          <div class="col-md-3"><div class="text-muted small">Branch</div><div class="fw-semibold">{{ detail.student_branch || '—' }}</div></div>
          <div class="col-md-2"><div class="text-muted small">CGPA</div><div class="fw-semibold">{{ detail.student_cgpa }}</div></div>
          <div class="col-md-4"><div class="text-muted small">Drive / Company</div><div class="fw-semibold">{{ detail.job_title }} · {{ detail.company_name }}</div></div>
        </div>

        <PipelineGraph :status="detail.status" :interviews="detail.interviews" :has-placement="!!detail.placement" />

        <div class="row g-3 mt-1">
          <div class="col-md-4">
            <label class="form-label">Status</label>
            <select v-model="detail.status" class="form-select">
              <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Offered Salary</label>
            <input v-model.number="detail.offered_salary" type="number" min="0" step="0.01" class="form-control" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Offered Joining Date</label>
            <input v-model="detail.offered_joining_date" type="date" class="form-control" />
          </div>
          <div class="col-12">
            <label class="form-label">Feedback</label>
            <textarea v-model="detail.feedback" class="form-control" rows="2"></textarea>
          </div>
        </div>

        <div class="d-flex flex-wrap gap-2 mt-3">
          <button v-if="detail.has_resume" type="button" class="btn btn-sm btn-outline-secondary" @click="downloadFile(`/admin/applications/${detail.id}/resume`, studentFileName(detail.student_name, 'resume.pdf'))">View Resume</button>
          <button v-if="detail.has_offer_letter" type="button" class="btn btn-sm btn-outline-secondary" @click="downloadFile(`/admin/applications/${detail.id}/offer-letter`, studentFileName(detail.student_name, 'offer_letter.pdf'))">View Offer Letter</button>
          <button type="submit" class="btn btn-sm btn-primary ms-auto" :disabled="saving">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
        </div>

        <div class="mt-4" v-if="detail.interviews.length">
          <div class="text-muted small mb-2">Interviews</div>
          <table class="table pp-table table-sm mb-0">
            <thead>
              <tr><th>Scheduled</th><th>Interviewer</th><th>Notes</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="iv in detail.interviews" :key="iv.id">
                <td>{{ formatDateTime(iv.scheduled_date_time) }}</td>
                <td>{{ iv.interviewer_name || 'Unassigned' }}</td>
                <td>{{ iv.notes || '—' }}</td>
                <td><StatusBadge :status="iv.status" /></td>
              </tr>
            </tbody>
          </table>
          <div class="text-muted small mt-2">Edit interview details from the Interviews page.</div>
        </div>
      </form>
    </Modal>
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import PipelineGraph from '@/components/shared/PipelineGraph.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDateTime } from '@/utils/date'
import { downloadFile, studentFileName } from '@/utils/download'
import { useRoute } from 'vue-router'

const STATUS_OPTIONS = ['APPLIED', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'PLACED', 'REJECTED', 'WITHDRAWN']

const route = useRoute()

const applications = ref([])
const companyOptions = ref([])
const driveOptions = ref([])
const search = ref('')
const companyIds = ref([])
const driveIds = ref([])
const statuses = ref([])

const viewOpen = ref(false)
const detail = ref(null)
const saving = ref(false)

// Shows which company/drive the list is currently pinned to, when arriving via a "View Applications" link.
const pinnedFilterLabel = computed(() => {
  if (driveIds.value.length === 1) {
    const match = driveOptions.value.find((d) => d.value === driveIds.value[0])
    if (match) return match.label
  }
  if (companyIds.value.length === 1) {
    const match = companyOptions.value.find((c) => c.value === companyIds.value[0])
    if (match) return match.label
  }
  return ''
})

// Fetches the application list for the active search/filter state.
async function load() {
  const { data } = await api.get('/admin/applications', {
    params: {
      search: search.value,
      company_ids: companyIds.value.join(','),
      drive_ids: driveIds.value.join(','),
      status: statuses.value.join(','),
    },
  })
  applications.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([search, companyIds, driveIds, statuses], debouncedLoad, { deep: true })

onMounted(async () => {
  const [companiesRes, drivesRes] = await Promise.all([
    api.get('/admin/companies'),
    api.get('/admin/drives'),
  ])
  companyOptions.value = companiesRes.data.results.map((c) => ({ value: c.id, label: c.company_name }))
  driveOptions.value = drivesRes.data.results.map((d) => ({ value: d.id, label: d.job_title }))
  // Pre-apply filters passed in via a "View Applications" link from Companies/Drives pages.
  if (route.query.company_id) {
    companyIds.value = [Number(route.query.company_id)]
  }
  if (route.query.drive_id) {
    driveIds.value = [Number(route.query.drive_id)]
  }
  await load()
})

// Opens the editable detail panel for an application.
async function openView(application) {
  const { data } = await api.get(`/admin/applications/${application.id}`)
  detail.value = data
  viewOpen.value = true
}

// Saves the editable application fields (status, feedback, offer details).
async function saveApplication() {
  saving.value = true
  try {
    const { data } = await api.patch(`/admin/applications/${detail.value.id}`, {
      status: detail.value.status,
      feedback: detail.value.feedback,
      offered_salary: detail.value.offered_salary,
      offered_joining_date: detail.value.offered_joining_date,
    })
    detail.value = data
    await load()
  } finally {
    saving.value = false
  }
}
</script>
