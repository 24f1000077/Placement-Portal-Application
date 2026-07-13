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
          <button
            class="btn btn-primary btn-sm mt-auto"
            :disabled="!d.eligible || d.already_applied"
            @click="openApply(d)"
          >{{ d.already_applied ? 'Already Applied' : 'Apply' }}</button>
        </div>
      </div>
      <div class="col-12" v-if="!drives.length"><p class="text-muted text-center py-4">No placement drives match your filters.</p></div>
    </div>

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

const drives = ref([])
const companyOptions = ref([])
const profile = ref(null)
const search = ref('')
const companyIds = ref([])
const skills = ref('')
const eligibleOnly = ref(false)

const applyOpen = ref(false)
const applyTarget = ref(null)
const applying = ref(false)

// Formats an ISO date string for display.
function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString() : '—'
}

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
  const seen = new Map()
  data.results.forEach((d) => seen.set(d.company_id, d.company_name))
  companyOptions.value = [...seen.entries()].map(([value, label]) => ({ value, label }))
}

const debouncedLoad = debounce(load, 300)
watch([search, companyIds, skills, eligibleOnly], debouncedLoad, { deep: true })

onMounted(async () => {
  const { data } = await api.get('/student/profile')
  profile.value = data
  await load()
})

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
