<template>
  <!-- Renders the company's placement drives with creation, filters, and lifecycle controls. -->
  <AppLayout>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="h4 mb-0">Placement Drives</h1>
      <button class="btn btn-primary" @click="openCreate">Create New Drive</button>
    </div>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <MultiSelectDropdown label="Status" :options="STATUS_OPTIONS" v-model="statuses" />
      <MultiSelectDropdown label="Branch" :options="branchOptions" v-model="branchFilter" />
      <input v-model="skills" type="search" class="form-control" style="max-width: 180px;" placeholder="Skills…" />
      <input v-model="minCgpa" type="number" min="0" max="10" step="0.1" class="form-control" style="max-width: 120px;" placeholder="Min CGPA" />
      <span class="text-muted small ms-auto">{{ drives.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr>
            <th>Job Title</th><th>Target Years</th><th>Deadline</th><th>Min CGPA</th><th>Status</th><th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in drives" :key="d.id">
            <td>{{ d.job_title }}</td>
            <td>{{ targetYearRange(d) }}</td>
            <td>{{ formatDateTime(d.application_deadline) }}</td>
            <td>{{ d.cgpa }}</td>
            <td><StatusBadge :status="d.status" /></td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openView(d)">View</button>
              <button class="btn btn-sm btn-outline-secondary me-1" @click="viewApplicants(d)">View Applicants</button>
              <template v-if="d.status === 'APPROVED'">
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openExtend(d)">Extend</button>
                <button class="btn btn-sm btn-outline-secondary me-1" @click="askConfirm(d, 'close')">Close Applications</button>
                <button class="btn btn-sm btn-outline-danger" @click="askConfirm(d, 'cancel')">Cancel</button>
              </template>
              <template v-else-if="d.status === 'APPLICATIONS_CLOSED'">
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openExtend(d)">Extend</button>
              </template>
            </td>
          </tr>
          <tr v-if="!drives.length"><td colspan="6" class="text-center text-muted py-4">No placement drives yet.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="formOpen" :title="formMode === 'create' ? 'Create Placement Drive' : 'Placement Drive'" full-width>
      <form class="row g-3" novalidate @submit.prevent="submitForm">
        <div v-if="formError" class="col-12"><div class="alert alert-danger py-2">{{ formError }}</div></div>
        <div class="col-md-6">
          <label class="form-label">Job Title</label>
          <input v-model="form.job_title" class="form-control" required :disabled="!editable" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Location</label>
          <input v-model="form.location" class="form-control" :disabled="!editable" />
        </div>
        <div class="col-12">
          <label class="form-label">Job Description</label>
          <textarea v-model="form.job_description" class="form-control" rows="3" :disabled="!editable"></textarea>
        </div>
        <div class="col-md-4">
          <label class="form-label">Minimum CGPA</label>
          <input v-model.number="form.cgpa" type="number" min="0" max="10" step="0.01" class="form-control" required :disabled="!editable" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Min Graduation Year</label>
          <select v-model.number="form.min_target_year" class="form-select" required :disabled="!editable">
            <option value="" disabled>Select</option>
            <option v-for="y in TARGET_YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Max Graduation Year</label>
          <select v-model.number="form.max_target_year" class="form-select" required :disabled="!editable">
            <option value="" disabled>Select</option>
            <option v-for="y in TARGET_YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">Offered Salary</label>
          <input v-model.number="form.salary" type="number" min="0" step="0.01" class="form-control" required :disabled="!editable" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Skills Required</label>
          <input v-model="form.skills_required" class="form-control" placeholder="e.g. Python, SQL" :disabled="!editable" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Application Deadline</label>
          <input v-model="form.application_deadline" type="datetime-local" class="form-control" :min="minDateTimeLocal" required :disabled="!editable" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Job Type</label>
          <input v-model="form.job_type" class="form-control" placeholder="e.g. Full-time" :disabled="!editable" />
        </div>
        <div class="col-12">
          <label class="form-label">Eligible Branches</label>
          <BranchTokenInput v-model="form.branch_ids" :options="branches" :allow-select-all="editable" />
        </div>
        <div class="col-12">
          <label class="form-label">Benefits / Notes</label>
          <textarea v-model="form.benefits" class="form-control" rows="2" :disabled="!editable"></textarea>
        </div>
        <div class="col-12" v-if="editable">
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Drive' }}</button>
        </div>
      </form>
    </Modal>

    <Modal v-model="extendOpen" title="Extend Application Deadline">
      <form @submit.prevent="saveExtend">
        <label class="form-label">New Deadline</label>
        <input v-model="extendValue" type="datetime-local" class="form-control" :min="minDateTimeLocal" required />
        <button type="submit" class="btn btn-primary mt-3">Extend Deadline</button>
      </form>
    </Modal>

    <ConfirmDialog v-model="confirmOpen" :title="confirmTitle" :message="confirmMessage" :confirm-label="confirmLabel" @confirm="runAction" />
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
const minDateTimeLocal = nowForDateTimeLocal()

const router = useRouter()

const drives = ref([])
const branches = ref([])
const statuses = ref([])
const branchFilter = ref([])
const skills = ref('')
const minCgpa = ref('')

// Branch names for the Branch filter dropdown.
const branchOptions = computed(() => branches.value.map((b) => b.name))

const formOpen = ref(false)
const formMode = ref('create')
const formError = ref('')
const saving = ref(false)
const editable = ref(true)
let editingId = null

// Returns a blank create-drive form state.
function blankForm() {
  return {
    job_title: '', job_description: '', location: '', job_type: '',
    cgpa: null, min_target_year: '', max_target_year: '', salary: null, skills_required: '', benefits: '',
    application_deadline: '', branch_ids: [],
  }
}
const form = ref(blankForm())

// Formats a drive's target-year range as a single value or "min–max".
function targetYearRange(drive) {
  return drive.min_target_year === drive.max_target_year
    ? String(drive.min_target_year)
    : `${drive.min_target_year}–${drive.max_target_year}`
}

const extendOpen = ref(false)
const extendValue = ref('')
let extendTarget = null

const confirmOpen = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmLabel = ref('Confirm')
let pendingAction = null
let pendingDrive = null

// Fetches the company's drive list for the active filter state.
async function load() {
  const { data } = await api.get('/company/drives', {
    params: {
      status: statuses.value.join(','),
      branches: branchFilter.value.join(','),
      skills: skills.value,
      min_cgpa: minCgpa.value || undefined,
    },
  })
  drives.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([statuses, branchFilter, skills, minCgpa], debouncedLoad, { deep: true })

onMounted(async () => {
  const { data } = await api.get('/auth/branches')
  branches.value = data
  await load()
})

// Navigates to Applications, pre-filtered to this drive.
function viewApplicants(drive) {
  router.push({ path: '/company/applications', query: { drive_id: drive.id } })
}

// Opens the creation form in a blank state.
function openCreate() {
  formMode.value = 'create'
  editable.value = true
  editingId = null
  formError.value = ''
  form.value = blankForm()
  formOpen.value = true
}

// Opens the view/edit form for an existing drive.
function openView(drive) {
  formMode.value = 'view'
  editable.value = drive.status === 'PENDING' || drive.status === 'REJECTED'
  editingId = drive.id
  formError.value = ''
  form.value = {
    ...drive,
    branch_ids: drive.allowed_branches.map((b) => b.id),
    application_deadline: drive.application_deadline ? drive.application_deadline.slice(0, 16) : '',
  }
  formOpen.value = true
}

// Submits the create/edit form to the API.
async function submitForm() {
  formError.value = ''
  saving.value = true
  try {
    if (editingId) {
      await api.patch(`/company/drives/${editingId}`, form.value)
    } else {
      await api.post('/company/drives', form.value)
    }
    formOpen.value = false
    await load()
  } catch (err) {
    formError.value = err.response?.data?.message || 'Unable to save the drive.'
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
  await api.post(`/company/drives/${extendTarget.id}/extend-deadline`, { application_deadline: extendValue.value })
  extendOpen.value = false
  await load()
}

const ACTION_COPY = {
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
  await api.post(`/company/drives/${pendingDrive.id}/${pendingAction}`)
  await load()
}
</script>
