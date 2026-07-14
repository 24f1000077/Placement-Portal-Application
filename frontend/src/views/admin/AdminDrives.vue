<template>
  <!-- Renders the admin placement drives management table with search, filters, and lifecycle actions. -->
  <AppLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h4 mb-0">Placement Drives</h1>
      <button class="btn btn-primary" @click="openCreate">Create Placement Drive</button>
    </div>

    <div v-if="companyFilterLabel" class="alert alert-info py-2 d-flex align-items-center justify-content-between mb-3">
      <span>Showing drives for <strong>{{ companyFilterLabel }}</strong></span>
      <button class="btn btn-sm btn-outline-secondary" @click="clearCompanyFilter">Clear filter</button>
    </div>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control" style="max-width: 240px;" placeholder="Search job title…" />
      <MultiSelectDropdown label="Company" :options="companyOptions" v-model="companyIds" />
      <MultiSelectDropdown label="Status" :options="STATUS_OPTIONS" v-model="statuses" />
      <MultiSelectDropdown label="Branch" :options="branchOptions" v-model="branchFilter" />
      <input v-model="skills" type="search" class="form-control" style="max-width: 180px;" placeholder="Skills…" />
      <input v-model="minCgpa" type="number" min="0" max="10" step="0.1" class="form-control" style="max-width: 120px;" placeholder="Min CGPA" />
      <input v-model="deadlineFrom" type="date" class="form-control" style="max-width: 160px;" title="Deadline from" />
      <input v-model="deadlineTo" type="date" class="form-control" style="max-width: 160px;" title="Deadline to" />
      <span class="text-muted small ms-auto">{{ drives.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr>
            <th>Job Title</th>
            <th>Company</th>
            <th>Target Years</th>
            <th>Deadline</th>
            <th>Min CGPA</th>
            <th>Status</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in drives" :key="d.id">
            <td>{{ d.job_title }}</td>
            <td>{{ d.company_name }}</td>
            <td>{{ targetYearRange(d) }}</td>
            <td>{{ formatDateTime(d.application_deadline) }}</td>
            <td>{{ d.cgpa }}</td>
            <td><StatusBadge :status="d.status" /></td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openView(d)">View</button>
              <button class="btn btn-sm btn-outline-secondary me-1" @click="viewApplications(d)">View Applications</button>
              <template v-if="d.status === 'PENDING'">
                <button class="btn btn-sm btn-outline-success me-1" @click="askConfirm(d, 'approve')">Approve</button>
                <button class="btn btn-sm btn-outline-danger" @click="askConfirm(d, 'reject')">Reject</button>
              </template>
              <template v-else-if="d.status === 'APPROVED'">
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openExtend(d)">Extend</button>
                <button class="btn btn-sm btn-outline-secondary me-1" @click="askConfirm(d, 'close')">Close Applications</button>
                <button class="btn btn-sm btn-outline-danger" @click="askConfirm(d, 'cancel')">Cancel</button>
              </template>
              <template v-else-if="d.status === 'APPLICATIONS_CLOSED'">
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openExtend(d)">Extend</button>
              </template>
            </td>
          </tr>
          <tr v-if="!drives.length"><td colspan="7" class="text-center text-muted py-4">No placement drives found.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="createOpen" title="Create Placement Drive" full-width>
      <form class="row g-3" @submit.prevent="submitCreate">
        <div v-if="createError" class="col-12"><div class="alert alert-danger py-2">{{ createError }}</div></div>
        <div class="col-md-6">
          <label class="form-label">Company</label>
          <select v-model.number="createForm.company_id" class="form-select" required>
            <option value="" disabled>Select a company</option>
            <option v-for="c in companyOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">Job Title</label>
          <input v-model="createForm.job_title" class="form-control" required />
        </div>
        <div class="col-md-12">
          <label class="form-label">Location</label>
          <input v-model="createForm.location" class="form-control" />
        </div>
        <div class="col-12">
          <label class="form-label">Job Description</label>
          <textarea v-model="createForm.job_description" class="form-control" rows="3"></textarea>
        </div>
        <div class="col-md-4">
          <label class="form-label">Minimum CGPA</label>
          <input v-model.number="createForm.cgpa" type="number" min="0" max="10" step="0.01" class="form-control" required />
        </div>
        <div class="col-md-4">
          <label class="form-label">Min Graduation Year</label>
          <select v-model.number="createForm.min_target_year" class="form-select">
            <option v-for="y in TARGET_YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Max Graduation Year</label>
          <select v-model.number="createForm.max_target_year" class="form-select">
            <option v-for="y in TARGET_YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Offered Salary</label>
          <input v-model.number="createForm.salary" type="number" min="0" step="0.01" class="form-control" required />
        </div>
        <div class="col-md-4">
          <label class="form-label">Skills Required</label>
          <input v-model="createForm.skills_required" class="form-control" placeholder="e.g. Python, SQL" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Experience Required</label>
          <input v-model="createForm.experience_required" class="form-control" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Application Deadline</label>
          <input v-model="createForm.application_deadline" type="datetime-local" class="form-control" :min="minDateTimeLocal" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Job Type</label>
          <input v-model="createForm.job_type" class="form-control" placeholder="e.g. Full-time" />
        </div>
        <div class="col-12">
          <label class="form-label">Eligible Branches</label>
          <BranchTokenInput v-model="createForm.branch_ids" :options="branches" />
        </div>
        <div class="col-12">
          <label class="form-label">Benefits</label>
          <textarea v-model="createForm.benefits" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12">
          <label class="form-label">Notes</label>
          <textarea v-model="createForm.notes" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12 text-muted small">This drive is created as Approved immediately, with no pending review step.</div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary" :disabled="creating">{{ creating ? 'Creating…' : 'Create Placement Drive' }}</button>
        </div>
      </form>
    </Modal>

    <Modal v-model="viewOpen" title="Placement Drive Details" full-width>
      <form v-if="editing" class="row g-3" @submit.prevent="saveEdit">
        <div class="col-md-6">
          <label class="form-label">Job Title</label>
          <input v-model="editing.job_title" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Location</label>
          <input v-model="editing.location" class="form-control" />
        </div>
        <div class="col-12">
          <label class="form-label">Job Description</label>
          <textarea v-model="editing.job_description" class="form-control" rows="3"></textarea>
        </div>
        <div class="col-md-4">
          <label class="form-label">Minimum CGPA</label>
          <input v-model.number="editing.cgpa" type="number" min="0" max="10" step="0.01" class="form-control" required />
        </div>
        <div class="col-md-4">
          <label class="form-label">Min Graduation Year</label>
          <select v-model.number="editing.min_target_year" class="form-select">
            <option v-for="y in TARGET_YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Max Graduation Year</label>
          <select v-model.number="editing.max_target_year" class="form-select">
            <option v-for="y in TARGET_YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Offered Salary</label>
          <input v-model.number="editing.salary" type="number" min="0" step="0.01" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Skills Required</label>
          <input v-model="editing.skills_required" class="form-control" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Application Deadline</label>
          <input v-model="editing.application_deadline" type="datetime-local" class="form-control" :min="minDateTimeLocal" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Job Type</label>
          <input v-model="editing.job_type" class="form-control" />
        </div>
        <div class="col-12">
          <label class="form-label">Eligible Branches</label>
          <BranchTokenInput v-model="editing.branch_ids" :options="branches" />
        </div>
        <div class="col-12">
          <label class="form-label">Notes</label>
          <textarea v-model="editing.notes" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12 text-muted small">
          Created {{ formatDateTime(editing.created_at) }} · Last updated {{ formatDateTime(editing.updated_at) }}
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
        </div>
      </form>
    </Modal>

    <Modal v-model="extendOpen" title="Extend Application Deadline">
      <form @submit.prevent="saveExtend">
        <label class="form-label">New Deadline</label>
        <input v-model="extendValue" type="datetime-local" class="form-control" :min="minDateTimeLocal" required />
        <button type="submit" class="btn btn-primary mt-3" :disabled="saving">Extend Deadline</button>
      </form>
    </Modal>

    <ConfirmDialog
      v-model="confirmOpen"
      :title="confirmTitle"
      :message="confirmMessage"
      :confirm-label="confirmLabel"
      @confirm="runAction"
    />
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import BranchTokenInput from '@/components/shared/BranchTokenInput.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDateTime, nowForDateTimeLocal } from '@/utils/date'

const STATUS_OPTIONS = ['PENDING', 'APPROVED', 'REJECTED', 'APPLICATIONS_CLOSED', 'CANCELLED']
const TARGET_YEARS = Array.from({ length: 8 }, (_, i) => 2026 + i)

// Formats a drive's target-year range as a single value or "min–max".
function targetYearRange(drive) {
  return drive.min_target_year === drive.max_target_year
    ? String(drive.min_target_year)
    : `${drive.min_target_year}–${drive.max_target_year}`
}

const route = useRoute()
const router = useRouter()

const drives = ref([])
const companyOptions = ref([])
const branches = ref([])
const search = ref('')
const companyIds = ref([])
const statuses = ref([])
const branchFilter = ref([])
const skills = ref('')
const minCgpa = ref('')
const deadlineFrom = ref('')
const deadlineTo = ref('')

const branchOptions = computed(() => branches.value.map((b) => b.name))

// Shows which company the list is currently pinned to, when arriving via a "View Drives" link.
const companyFilterLabel = computed(() => {
  if (companyIds.value.length !== 1) return ''
  const match = companyOptions.value.find((c) => c.value === companyIds.value[0])
  return match ? match.label : ''
})

// Removes the company filter pinned via a "View Drives" link.
function clearCompanyFilter() {
  companyIds.value = []
}

const viewOpen = ref(false)
const editing = ref(null)
const saving = ref(false)

const createOpen = ref(false)
const creating = ref(false)
const createError = ref('')
function blankCreateForm() {
  return {
    company_id: '', job_title: '', location: '', job_description: '',
    cgpa: null, min_target_year: TARGET_YEARS[0], max_target_year: TARGET_YEARS[0],
    salary: null, skills_required: '', experience_required: '', application_deadline: '',
    job_type: '', branch_ids: [], benefits: '', notes: '',
  }
}
const createForm = ref(blankCreateForm())

const extendOpen = ref(false)
const extendValue = ref('')
let extendTarget = null

const confirmOpen = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmLabel = ref('Confirm')
let pendingAction = null
let pendingDrive = null

const minDateTimeLocal = computed(() => nowForDateTimeLocal())

// Fetches the drive list for the active search/filter state.
async function load() {
  const { data } = await api.get('/admin/drives', {
    params: {
      search: search.value,
      company_ids: companyIds.value.join(','),
      status: statuses.value.join(','),
      branches: branchFilter.value.join(','),
      skills: skills.value,
      min_cgpa: minCgpa.value || undefined,
      deadline_from: deadlineFrom.value || undefined,
      deadline_to: deadlineTo.value || undefined,
    },
  })
  drives.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([search, companyIds, statuses, branchFilter, skills, minCgpa, deadlineFrom, deadlineTo], debouncedLoad, { deep: true })

onMounted(async () => {
  const [companiesRes, branchesRes] = await Promise.all([
    api.get('/admin/companies'),
    api.get('/auth/branches'),
  ])
  companyOptions.value = companiesRes.data.results.map((c) => ({ value: c.id, label: c.company_name }))
  branches.value = branchesRes.data
  // Pre-apply a company filter passed in via a "View Drives" link from the Companies page.
  if (route.query.company_id) {
    companyIds.value = [Number(route.query.company_id)]
  }
  await load()
})

// Navigates to Applications, pre-filtered to this drive.
function viewApplications(drive) {
  router.push({ path: '/admin/applications', query: { drive_id: drive.id } })
}

// Opens the create-drive modal in a blank state.
function openCreate() {
  createForm.value = blankCreateForm()
  createError.value = ''
  createOpen.value = true
}

// Submits the new placement drive; created directly as Approved.
async function submitCreate() {
  creating.value = true
  createError.value = ''
  try {
    await api.post('/admin/drives', createForm.value)
    createOpen.value = false
    await load()
  } catch (err) {
    createError.value = err.response?.data?.message || 'Unable to create the placement drive.'
  } finally {
    creating.value = false
  }
}

// Opens the full-width detail/edit modal for a drive.
function openView(drive) {
  editing.value = {
    ...drive,
    branch_ids: drive.allowed_branches.map((b) => b.id),
    application_deadline: drive.application_deadline ? drive.application_deadline.slice(0, 16) : '',
  }
  viewOpen.value = true
}

// Saves the edited drive fields.
async function saveEdit() {
  saving.value = true
  try {
    await api.patch(`/admin/drives/${editing.value.id}`, editing.value)
    viewOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}

// Opens the deadline-extension modal for a drive.
function openExtend(drive) {
  extendTarget = drive
  extendValue.value = ''
  extendOpen.value = true
}

// Submits the extended deadline.
async function saveExtend() {
  saving.value = true
  try {
    await api.post(`/admin/drives/${extendTarget.id}/extend-deadline`, { application_deadline: extendValue.value })
    extendOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const ACTION_COPY = {
  approve: { title: 'Approve Drive', message: 'Students will be able to see and apply to this drive. Continue?', label: 'Approve' },
  reject: { title: 'Reject Drive', message: 'This rejects the placement drive request. Continue?', label: 'Reject' },
  close: { title: 'Close Applications', message: 'This stops new applications to this drive. Continue?', label: 'Close Applications' },
  cancel: { title: 'Cancel Drive', message: 'This cancels the drive and rejects all active applications. Continue?', label: 'Cancel' },
}

// Opens the confirmation dialog for a given row action.
function askConfirm(drive, action) {
  pendingDrive = drive
  pendingAction = action
  const copy = ACTION_COPY[action]
  confirmTitle.value = copy.title
  confirmMessage.value = copy.message
  confirmLabel.value = copy.label
  confirmOpen.value = true
}

// Executes the confirmed lifecycle action against the API.
async function runAction() {
  await api.post(`/admin/drives/${pendingDrive.id}/${pendingAction}`)
  await load()
}
</script>
