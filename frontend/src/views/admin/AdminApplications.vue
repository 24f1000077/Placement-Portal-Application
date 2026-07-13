<template>
  <!-- Renders the admin applications table with a single unified read-only view panel. -->
  <AppLayout>
    <h1 class="h4 mb-4">Applications</h1>

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
      <div v-if="detail">
        <div class="row g-3 mb-4">
          <div class="col-md-3"><div class="text-muted small">Student</div><div class="fw-semibold">{{ detail.student_name }}</div></div>
          <div class="col-md-3"><div class="text-muted small">Branch</div><div class="fw-semibold">{{ detail.student_branch || '—' }}</div></div>
          <div class="col-md-2"><div class="text-muted small">CGPA</div><div class="fw-semibold">{{ detail.student_cgpa }}</div></div>
          <div class="col-md-4"><div class="text-muted small">Drive / Company</div><div class="fw-semibold">{{ detail.job_title }} · {{ detail.company_name }}</div></div>
        </div>

        <PipelineGraph :status="detail.status" :interviews="detail.interviews" :has-placement="!!detail.placement" />

        <div class="mt-4" v-if="detail.feedback">
          <div class="alert alert-secondary py-2 mb-0">{{ detail.feedback }}</div>
        </div>

        <div class="d-flex flex-wrap gap-2 mt-4">
          <button v-if="detail.has_resume" class="btn btn-sm btn-outline-secondary" @click="downloadFile(`/admin/applications/${detail.id}/resume`, 'resume.pdf')">View Resume</button>
          <button v-if="detail.has_offer_letter" class="btn btn-sm btn-outline-secondary" @click="downloadFile(`/admin/applications/${detail.id}/offer-letter`, 'offer_letter.pdf')">View Offer Letter</button>
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
        </div>
      </div>
    </Modal>
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import PipelineGraph from '@/components/shared/PipelineGraph.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDateTime } from '@/utils/date'
import { downloadFile } from '@/utils/download'

const STATUS_OPTIONS = ['APPLIED', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'PLACED', 'REJECTED', 'WITHDRAWN']

const applications = ref([])
const companyOptions = ref([])
const driveOptions = ref([])
const search = ref('')
const companyIds = ref([])
const driveIds = ref([])
const statuses = ref([])

const viewOpen = ref(false)
const detail = ref(null)

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
  await load()
})

// Opens the unified read-only detail panel for an application.
async function openView(application) {
  const { data } = await api.get(`/admin/applications/${application.id}`)
  detail.value = data
  viewOpen.value = true
}
</script>
