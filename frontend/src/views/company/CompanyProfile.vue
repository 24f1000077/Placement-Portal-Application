<template>
  <!-- Renders the full-width company profile editing panel. -->
  <AppLayout>
    <h1 class="h4 mb-4">Company Profile</h1>
    <div class="pp-card p-4" style="max-width: 720px;">
      <div v-if="saved" class="alert alert-success py-2">Profile updated.</div>
      <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
      <form v-if="form" class="row g-3" novalidate @submit.prevent="save">
        <div class="col-md-6">
          <label class="form-label">HR Contact Name</label>
          <input v-model="form.name" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Email</label>
          <input :value="form.email" class="form-control" disabled />
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
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/shared/AppLayout.vue'
import api from '@/services/api'

const form = ref(null)
const saving = ref(false)
const saved = ref(false)
const formError = ref('')
const passwords = ref({ current_password: '', new_password: '' })

// Loads the company's current profile into the form.
onMounted(async () => {
  const { data } = await api.get('/company/profile')
  form.value = data
})

// Saves the edited profile fields and an optional password change.
async function save() {
  saving.value = true
  saved.value = false
  formError.value = ''
  try {
    const payload = { ...form.value }
    if (passwords.value.new_password) {
      payload.current_password = passwords.value.current_password
      payload.new_password = passwords.value.new_password
    }
    const { data } = await api.patch('/company/profile', payload)
    form.value = data
    passwords.value = { current_password: '', new_password: '' }
    saved.value = true
  } catch (err) {
    formError.value = err.response?.data?.message || 'Could not save your changes.'
  } finally {
    saving.value = false
  }
}
</script>
