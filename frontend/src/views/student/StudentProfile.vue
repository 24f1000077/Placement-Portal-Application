<template>
  <!-- Renders the full-width student profile editing panel. -->
  <AppLayout>
    <h1 class="h4 mb-4">Profile</h1>
    <div class="pp-card p-4" style="max-width: 760px;">
      <div v-if="saved" class="alert alert-success py-2">Profile updated.</div>
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <form v-if="form" class="row g-3" novalidate @submit.prevent="save">
        <div class="col-md-6">
          <label class="form-label">Full Name</label>
          <input v-model="form.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Email</label>
          <input :value="form.email" class="form-control" disabled />
        </div>
        <div class="col-md-4">
          <label class="form-label">Contact Number</label>
          <input v-model="form.contact_number" class="form-control" pattern="\d{7,15}" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Branch</label>
          <input :value="form.branch" class="form-control" disabled />
        </div>
        <div class="col-md-4">
          <label class="form-label">Graduation Year</label>
          <input :value="form.graduation_year" class="form-control" disabled />
        </div>
        <div class="col-md-4">
          <label class="form-label">CGPA</label>
          <input v-model="form.cgpa" type="number" min="0" max="10" step="0.01" class="form-control" required />
        </div>
        <div class="col-12">
          <label class="form-label">Skills</label>
          <input v-model="form.skills" class="form-control" placeholder="e.g. Python, SQL, React" />
        </div>
        <div class="col-12">
          <label class="form-label">Project Experience</label>
          <textarea v-model="form.experience" class="form-control" rows="4"></textarea>
        </div>
        <div class="col-12">
          <label class="form-label">Resume (PDF)</label>
          <input type="file" accept="application/pdf" class="form-control" @change="onResumeFile" />
          <button v-if="form.has_resume" type="button" class="btn btn-link btn-sm px-0 mt-1" @click="downloadFile('/student/profile/resume', resumeFilename)">Download current resume</button>
        </div>

        <div class="col-12">
          <hr />
          <h2 class="h6 mb-2">Change Password</h2>
          <p class="text-muted small mb-3">Leave these blank to keep your current password.</p>
        </div>
        <div class="col-md-6">
          <label class="form-label">Current Password</label>
          <input v-model="passwords.current_password" type="password" class="form-control" autocomplete="current-password" />
        </div>
        <div class="col-md-6">
          <label class="form-label">New Password</label>
          <input v-model="passwords.new_password" type="password" class="form-control" minlength="6" autocomplete="new-password" />
        </div>

        <div class="col-12">
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import api from '@/services/api'
import { downloadFile, studentFileName } from '@/utils/download'

const form = ref(null)
const saving = ref(false)
const saved = ref(false)
const formError = ref('')
const passwords = ref({ current_password: '', new_password: '' })
let resumeFile = null

const resumeFilename = computed(() => studentFileName(form.value?.name, 'resume.pdf'))

// Loads the student's current profile into the form.
onMounted(async () => {
  const { data } = await api.get('/student/profile')
  form.value = data
})

// Captures the selected resume PDF file.
function onResumeFile(evt) {
  resumeFile = evt.target.files[0] || null
}

// Saves the edited profile fields, an optional resume upload, and an optional password change.
async function save() {
  saving.value = true
  saved.value = false
  formError.value = ''
  try {
    const payload = new FormData()
    payload.append('name', form.value.name)
    payload.append('contact_number', form.value.contact_number || '')
    payload.append('cgpa', form.value.cgpa)
    payload.append('skills', form.value.skills || '')
    payload.append('experience', form.value.experience || '')
    if (resumeFile) payload.append('resume', resumeFile)
    if (passwords.value.new_password) {
      payload.append('current_password', passwords.value.current_password)
      payload.append('new_password', passwords.value.new_password)
    }
    const { data } = await api.patch('/student/profile', payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    form.value = data
    resumeFile = null
    passwords.value = { current_password: '', new_password: '' }
    saved.value = true
  } catch (err) {
    formError.value = err.response?.data?.message || 'Could not save your changes.'
  } finally {
    saving.value = false
  }
}
</script>
