<template>
  <!-- Renders the approved placement drives students can browse and apply to. -->
  <AppLayout>
    <h1 class="h4 mb-4">Placement Drives</h1>

    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input v-model="search" type="search" class="form-control pp-search-pill" style="max-width: 280px;" placeholder="Search title or description…" />
      <MultiSelectDropdown label="Company" :options="companyOptions" v-model="companyIds" />
      <input v-model="skills" type="search" class="form-control" style="max-width: 180px;" placeholder="Skills…" />
      <div class="form-check ms-2">
        <input class="form-check-input" type="checkbox" id="eligibleOnly" v-model="eligibleOnly" />
        <label class="form-check-label" for="eligibleOnly">Eligible drives only</label>
      </div>
      <span class="text-muted small ms-auto">{{ drives.length }} record(s)</span>
    </div>

    <div class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="d in drives" :key="d.id">
        <div class="pp-card p-3 h-100 d-flex flex-column">
          <div class="d-flex justify-content-between align-items-start mb-1">
            <h2 class="h6 mb-0">{{ d.job_title }}</h2>
            <StatusBadge v-if="!d.eligible" status="Not Eligible" />
          </div>
          <div class="text-muted small mb-2">{{ d.company_name }} · {{ d.location || 'Location TBD' }}</div>
          <p class="small flex-grow-1">{{ d.job_description }}</p>
          <div class="small text-muted mb-2">
            Min CGPA: {{ d.cgpa }} · Target Year: {{ d.target_year }} · Deadline: {{ formatDate(d.application_deadline) }}
          </div>
          <div class="d-flex gap-2 mt-auto">
            <button class="btn btn-outline-secondary btn-sm flex-grow-1" @click="openView(d)">View Details</button>
            <button
              v-if="d.eligible && !d.already_applied && !d.deadline_passed"
              class="btn btn-primary btn-sm flex-grow-1"
              @click="openApply(d)"
            >Apply</button>
          </div>
        </div>
      </div>
      <div class="col-12" v-if="!drives.length"><p class="text-muted text-center py-4">No placement drives match your filters.</p></div>
    </div>

    <Modal v-model="detailOpen" title="Placement Drive Details">
      <div v-if="detailTarget">
        <h2 class="h5">{{ detailTarget.job_title }}</h2>
        <div class="text-muted small mb-3">{{ detailTarget.company_name }} · {{ detailTarget.location || 'Location TBD' }}</div>
        <p>{{ detailTarget.job_description }}</p>
        <div class="row g-2 small mb-3">
          <div class="col-6"><span class="text-muted">Minimum CGPA:</span> {{ detailTarget.cgpa }}</div>
          <div class="col-6"><span class="text-muted">Target Year:</span> {{ detailTarget.target_year }}</div>
          <div class="col-6"><span class="text-muted">Deadline:</span> {{ formatDateTime(detailTarget.application_deadline) }}</div>
          <div class="col-6"><span class="text-muted">Salary:</span> {{ detailTarget.salary }}</div>
          <div class="col-12"><span class="text-muted">Skills:</span> {{ detailTarget.skills_required || '—' }}</div>
          <div class="col-12"><span class="text-muted">Eligible Branches:</span> {{ detailTarget.allowed_branches.map(b => b.name).join(', ') || 'All branches' }}</div>
        </div>

        <div v-if="detailTarget.ineligibility_reasons.length" class="alert alert-warning py-2">
          <div class="fw-semibold mb-1">You are not eligible for this drive:</div>
          <ul class="mb-0 ps-3">
            <li v-for="(reason, i) in detailTarget.ineligibility_reasons" :key="i">{{ reason }}</li>
          </ul>
        </div>

        <button
          v-if="detailTarget.eligible && !detailTarget.already_applied && !detailTarget.deadline_passed"
          class="btn btn-primary"
          @click="detailOpen = false; openApply(detailTarget)"
        >Apply</button>
        <div v-else-if="detailTarget.already_applied" class="text-muted small">You have already applied to this drive.</div>
        <div v-else-if="detailTarget.deadline_passed" class="text-muted small">The application deadline has passed.</div>
      </div>
    </Modal>

    <Modal v-model="applyOpen" title="Confirm Application">
      <div v-if="applyTarget">
        <p>You're applying to <strong>{{ applyTarget.job_title }}</strong> at <strong>{{ applyTarget.company_name }}</strong>.</p>
        <div class="pp-card p-3 mb-3">
          <div class="text-muted small mb-2">Your Profile Snapshot</div>
          <div class="small">CGPA: {{ profile?.cgpa }} · Branch: {{ profile?.branch }} · Graduation Year: {{ profile?.graduation_year }}</div>
        </div>
        <button class="btn btn-primary" :disabled="applying" @click="confirmApply">
          {{ applying ? 'Submitting…' : 'Confirm & Apply' }}
        </button>
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
import api from '@/services/api'
import { debounce } from '@/utils/debounce'
import { formatDate, formatDateTime } from '@/utils/date'

const drives = ref([])
const companyOptions = ref([])
const profile = ref(null)
const search = ref('')
const companyIds = ref([])
const skills = ref('')
const eligibleOnly = ref(false)

const detailOpen = ref(false)
const detailTarget = ref(null)

const applyOpen = ref(false)
const applyTarget = ref(null)
const applying = ref(false)

// Fetches the approved drive list for the active search/filter state.
async function load() {
  const { data } = await api.get('/student/drives', {
    params: {
      search: search.value,
      company_ids: companyIds.value.join(','),
      skills: skills.value,
      eligible_only: eligibleOnly.value,
    },
  })
  drives.value = data.results
}

const debouncedLoad = debounce(load, 300)
watch([search, companyIds, skills, eligibleOnly], debouncedLoad, { deep: true })

onMounted(async () => {
  const [profileRes, companiesRes] = await Promise.all([
    api.get('/student/profile'),
    api.get('/student/companies'),
  ])
  profile.value = profileRes.data
  companyOptions.value = companiesRes.data.map((c) => ({ value: c.id, label: c.name }))
  await load()
})

// Opens the drive detail modal, available regardless of eligibility.
function openView(drive) {
  detailTarget.value = drive
  detailOpen.value = true
}

// Opens the application confirmation modal for a drive.
function openApply(drive) {
  applyTarget.value = drive
  applyOpen.value = true
}

// Submits the confirmed application.
async function confirmApply() {
  applying.value = true
  try {
    await api.post(`/student/drives/${applyTarget.value.id}/apply`)
    applyOpen.value = false
    await load()
  } finally {
    applying.value = false
  }
}
</script>
