<template>
  <!-- Renders the admin companies management table with search, filters, and actions. -->
  <AppLayout>
    <h1 class="h4 mb-4">Companies</h1>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control" style="max-width: 280px;" placeholder="Search company name…" />
      <MultiSelectDropdown label="Status" :options="STATUS_OPTIONS" v-model="statuses" />
      <span class="text-muted small ms-auto">{{ companies.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr>
            <th>Company Name</th>
            <th>Industry</th>
            <th>HR Contact Email</th>
            <th>Status</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in companies" :key="c.id">
            <td>{{ c.company_name }}</td>
            <td>{{ c.industry || '—' }}</td>
            <td>{{ c.email }}</td>
            <td><StatusBadge :status="c.approval_status" /></td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openView(c)">View</button>
              <button class="btn btn-sm btn-outline-secondary me-1" @click="viewDrives(c)">View Drives</button>
              <button class="btn btn-sm btn-outline-secondary me-1" @click="viewApplications(c)">View Applications</button>
              <template v-if="c.approval_status === 'PENDING'">
                <button class="btn btn-sm btn-outline-success me-1" @click="askConfirm(c, 'approve')">Accept</button>
                <button class="btn btn-sm btn-outline-danger" @click="askConfirm(c, 'reject')">Reject</button>
              </template>
              <template v-else-if="c.approval_status === 'APPROVED'">
                <button class="btn btn-sm btn-outline-danger" @click="askConfirm(c, 'blacklist')">Blacklist</button>
              </template>
              <template v-else-if="c.approval_status === 'BLACKLISTED'">
                <button class="btn btn-sm btn-outline-success" @click="askConfirm(c, 'whitelist')">Whitelist</button>
              </template>
            </td>
          </tr>
          <tr v-if="!companies.length"><td colspan="5" class="text-center text-muted py-4">No companies found.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="viewOpen" title="Company Details" full-width>
      <form v-if="editing" class="row g-3" @submit.prevent="saveEdit">
        <div class="col-md-6">
          <label class="form-label">Contact Person Name</label>
          <input v-model="editing.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Email</label>
          <input v-model="editing.email" type="email" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Company Name</label>
          <input v-model="editing.company_name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">HR Contact Number</label>
          <input v-model="editing.hr_contact" class="form-control" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Industry</label>
          <input v-model="editing.industry" class="form-control" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Website</label>
          <input v-model="editing.website" type="url" class="form-control" />
        </div>
        <div class="col-12 text-muted small">
          Registered {{ formatDateTime(editing.account_created_at) }} · Last updated {{ formatDateTime(editing.account_updated_at) }}
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
        </div>
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
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import MultiSelectDropdown from '@/components/shared/MultiSelectDropdown.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDateTime } from '@/utils/date'

const STATUS_OPTIONS = ['PENDING', 'APPROVED', 'REJECTED', 'BLACKLISTED']

const router = useRouter()

const companies = ref([])
const search = ref('')
const statuses = ref([])

const viewOpen = ref(false)
const editing = ref(null)
const saving = ref(false)

const confirmOpen = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmLabel = ref('Confirm')
let pendingAction = null
let pendingCompany = null

// Fetches the company list for the active search/filter state.
async function load() {
  const { data } = await api.get('/admin/companies', {
    params: { search: search.value, status: statuses.value.join(',') },
  })
  companies.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([search, statuses], debouncedLoad, { deep: true })
onMounted(load)

// Navigates to Placement Drives, pre-filtered to this company.
function viewDrives(company) {
  router.push({ path: '/admin/drives', query: { company_id: company.id } })
}

// Navigates to Applications, pre-filtered to this company.
function viewApplications(company) {
  router.push({ path: '/admin/applications', query: { company_id: company.id } })
}

// Opens the full-width detail/edit modal for a company.
function openView(company) {
  editing.value = { ...company }
  viewOpen.value = true
}

// Saves the edited company profile fields.
async function saveEdit() {
  saving.value = true
  try {
    await api.patch(`/admin/companies/${editing.value.id}`, editing.value)
    viewOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const ACTION_COPY = {
  approve: { title: 'Approve Company', message: 'This grants the company access to create placement drives. Continue?', label: 'Approve' },
  reject: { title: 'Reject Company', message: 'This rejects the company\'s registration request. Continue?', label: 'Reject' },
  blacklist: { title: 'Blacklist Company', message: 'This disables the company\'s login, cancels its active drives, and rejects active applications. Continue?', label: 'Blacklist' },
  whitelist: { title: 'Whitelist Company', message: 'This restores the company\'s approved access. Continue?', label: 'Whitelist' },
}

// Opens the confirmation dialog for a given row action.
function askConfirm(company, action) {
  pendingCompany = company
  pendingAction = action
  const copy = ACTION_COPY[action]
  confirmTitle.value = copy.title
  confirmMessage.value = copy.message
  confirmLabel.value = copy.label
  confirmOpen.value = true
}

// Executes the confirmed action against the API.
async function runAction() {
  await api.post(`/admin/companies/${pendingCompany.id}/${pendingAction}`)
  await load()
}
</script>
