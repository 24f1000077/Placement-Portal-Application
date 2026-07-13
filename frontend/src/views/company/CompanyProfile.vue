<template>
  <!-- Renders the full-width company profile editing panel. -->
  <AppLayout>
    <h1 class="h4 mb-4">Company Profile</h1>
    <div class="pp-card p-4" style="max-width: 720px;">
      <div v-if="saved" class="alert alert-success py-2">Profile updated.</div>
      <form v-if="form" class="row g-3" @submit.prevent="save">
        <div class="col-md-6">
          <label class="form-label">HR Contact Name</label>
          <input v-model="form.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Company Name</label>
          <input v-model="form.company_name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">HR Contact Number</label>
          <input v-model="form.hr_contact" class="form-control" pattern="\d{7,15}" />
        </div>
        <div class="col-md-6">
          <label class="form-label">Industry</label>
          <input v-model="form.industry" class="form-control" />
        </div>
        <div class="col-12">
          <label class="form-label">Website</label>
          <input v-model="form.website" type="url" class="form-control" placeholder="https://" />
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

const form = ref(null)
const saving = ref(false)
const saved = ref(false)

// Loads the company's current profile into the form.
onMounted(async () => {
  const { data } = await api.get('/company/profile')
  form.value = data
})

// Saves the edited profile fields.
async function save() {
  saving.value = true
  saved.value = false
  try {
    const { data } = await api.patch('/company/profile', form.value)
    form.value = data
    saved.value = true
  } finally {
    saving.value = false
  }
}
</script>
