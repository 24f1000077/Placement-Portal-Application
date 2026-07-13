<template>
  <!-- Renders the full-width student profile editing panel. -->
  <AppLayout>
    <h1 class="h4 mb-4">Profile</h1>
    <div class="pp-card p-4" style="max-width: 760px;">
      <div v-if="saved" class="alert alert-success py-2">Profile updated.</div>
      <form v-if="form" class="row g-3" @submit.prevent="save">
        <div class="col-md-6">
          <label class="form-label">Full Name</label>
          <input v-model="form.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Contact Number</label>
          <input v-model="form.contact_number" class="form-control" pattern="\d{7,15}" />
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
          <button v-if="form.has_resume" type="button" class="btn btn-link btn-sm px-0 mt-1" @click="downloadFile('/student/profile/resume', 'resume.pdf')">Download current resume</button>
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import api from '@/services/api'
import { downloadFile } from '@/utils/download'

const form = ref(null)
const saving = ref(false)
const saved = ref(false)
let resumeFile = null

// Loads the student's current profile into the form.
onMounted(async () => {
  const { data } = await api.get('/student/profile')
  form.value = data
})

// Captures the selected resume PDF file.
function onResumeFile(evt) {
  resumeFile = evt.target.files[0] || null
}

// Saves the edited profile fields, including an optional resume upload.
async function save() {
  saving.value = true
  saved.value = false
  try {
    const payload = new FormData()
    payload.append('name', form.value.name)
    payload.append('contact_number', form.value.contact_number || '')
    payload.append('skills', form.value.skills || '')
    payload.append('experience', form.value.experience || '')
    if (resumeFile) payload.append('resume', resumeFile)
    const { data } = await api.patch('/student/profile', payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    form.value = data
    resumeFile = null
    saved.value = true
  } finally {
    saving.value = false
  }
}
</script>
