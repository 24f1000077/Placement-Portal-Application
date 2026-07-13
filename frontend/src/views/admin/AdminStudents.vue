<template>
  <!-- Renders the admin students management table with search and blacklist controls. -->
  <AppLayout>
    <h1 class="h4 mb-4">Students</h1>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control" style="max-width: 280px;" placeholder="Search student name…" />
      <span class="text-muted small ms-auto">{{ students.length }} record(s)</span>
    </div>

    <div class="pp-card">
      <table class="table pp-table mb-0 align-middle">
        <thead>
          <tr>
            <th>Full Name</th>
            <th>Student ID</th>
            <th>Branch</th>
            <th>CGPA</th>
            <th>Status</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in students" :key="s.id">
            <td>{{ s.name }}</td>
            <td>{{ s.id }}</td>
            <td>{{ s.branch || '—' }}</td>
            <td>{{ s.cgpa }}</td>
            <td><StatusBadge :status="s.approval_status" /></td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openView(s)">View</button>
              <button
                v-if="s.approval_status === 'APPROVED'"
                class="btn btn-sm btn-outline-danger"
                @click="askConfirm(s, 'blacklist')"
              >Blacklist</button>
              <button
                v-else
                class="btn btn-sm btn-outline-success"
                @click="askConfirm(s, 'whitelist')"
              >Whitelist</button>
            </td>
          </tr>
          <tr v-if="!students.length"><td colspan="6" class="text-center text-muted py-4">No students found.</td></tr>
        </tbody>
      </table>
    </div>

    <Modal v-model="viewOpen" title="Student Details" full-width>
      <form v-if="editing" class="row g-3" @submit.prevent="saveEdit">
        <div class="col-md-6">
          <label class="form-label">Full Name</label>
          <input v-model="editing.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Email</label>
          <input v-model="editing.email" type="email" class="form-control" required />
        </div>
        <div class="col-md-4">
          <label class="form-label">Contact Number</label>
          <input v-model="editing.contact_number" class="form-control" />
        </div>
        <div class="col-md-4">
          <label class="form-label">CGPA</label>
          <input v-model.number="editing.cgpa" type="number" min="0" max="10" step="0.01" class="form-control" required />
        </div>
        <div class="col-md-4">
          <label class="form-label">Graduation Year</label>
          <input v-model.number="editing.graduation_year" type="number" min="2020" max="2035" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Branch</label>
          <select v-model.number="editing.branch_id" class="form-select">
            <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">Skills</label>
          <input v-model="editing.skills" class="form-control" />
        </div>
        <div class="col-12">
          <label class="form-label">Experience</label>
          <textarea v-model="editing.experience" class="form-control" rows="2"></textarea>
        </div>
        <div class="col-12">
          <button v-if="editing.has_resume" type="button" class="btn btn-outline-secondary me-2" @click="downloadFile(`/admin/students/${editing.id}/resume`, 'resume.pdf')">Download Resume</button>
          <span v-else class="text-muted small me-2">No resume uploaded.</span>
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
import AppLayout from '@/components/shared/AppLayout.vue'
import Modal from '@/components/shared/Modal.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { downloadFile } from '@/utils/download'

const students = ref([])
const branches = ref([])
const search = ref('')

const viewOpen = ref(false)
const editing = ref(null)
const saving = ref(false)

const confirmOpen = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmLabel = ref('Confirm')
let pendingAction = null
let pendingStudent = null

// Fetches the student list for the active search state.
async function load() {
  const { data } = await api.get('/admin/students', { params: { search: search.value } })
  students.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch(search, debouncedLoad)

onMounted(async () => {
  const { data } = await api.get('/auth/branches')
  branches.value = data
  await load()
})

// Opens the full-width detail/edit modal for a student.
function openView(student) {
  editing.value = { ...student }
  viewOpen.value = true
}

// Saves the edited student profile fields.
async function saveEdit() {
  saving.value = true
  try {
    await api.patch(`/admin/students/${editing.value.id}`, editing.value)
    viewOpen.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const ACTION_COPY = {
  blacklist: { title: 'Blacklist Student', message: 'This disables the student\'s login and withdraws their active applications. Continue?', label: 'Blacklist' },
  whitelist: { title: 'Whitelist Student', message: 'This restores the student\'s account access. Continue?', label: 'Whitelist' },
}

// Opens the confirmation dialog for a given row action.
function askConfirm(student, action) {
  pendingStudent = student
  pendingAction = action
  const copy = ACTION_COPY[action]
  confirmTitle.value = copy.title
  confirmMessage.value = copy.message
  confirmLabel.value = copy.label
  confirmOpen.value = true
}

// Executes the confirmed action against the API.
async function runAction() {
  await api.post(`/admin/students/${pendingStudent.id}/${pendingAction}`)
  await load()
}
</script>
