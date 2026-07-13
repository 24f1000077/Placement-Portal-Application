<template>
  <!-- Renders the company self-registration form. -->
  <div class="pp-auth-shell">
    <div class="pp-card pp-auth-card" style="max-width: 560px;">
      <div class="pp-auth-brand">PlacementPro</div>
      <p class="text-muted mb-4">Register your company</p>

      <div v-if="errorMessage" class="alert alert-danger py-2">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success py-2">{{ successMessage }}</div>

      <form novalidate @submit.prevent="onSubmit">
        <div class="row g-3">
          <div class="col-12">
            <label class="form-label">Company Name</label>
            <input v-model.trim="form.company_name" type="text" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">HR Contact Name</label>
            <input v-model.trim="form.name" type="text" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">HR Contact Number</label>
            <input v-model.trim="form.hr_contact" type="tel" class="form-control" pattern="\d{7,15}" title="Digits only, 7-15 characters" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Email address</label>
            <input v-model.trim="form.email" type="email" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Industry</label>
            <input v-model.trim="form.industry" type="text" class="form-control" placeholder="e.g. Software" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Website</label>
            <input v-model.trim="form.website" type="url" class="form-control" placeholder="https://" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" required minlength="6" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Confirm Password</label>
            <input v-model="confirmPassword" type="password" class="form-control" required minlength="6" />
          </div>
        </div>

        <button type="submit" class="btn btn-primary w-100 mt-4" :disabled="submitting || passwordMismatch">
          {{ submitting ? 'Submitting…' : 'Register' }}
        </button>
        <div v-if="passwordMismatch" class="text-danger small mt-2">Passwords do not match.</div>
        <p class="text-muted small mt-3 mb-0">Your account will be reviewed by the placement cell before you can sign in.</p>
      </form>

      <div class="text-center mt-4 small">
        <span class="text-muted">Already have an account?</span>
        <router-link to="/login" class="ms-1">Sign In</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const confirmPassword = ref('')

const form = reactive({
  name: '', email: '', password: '', company_name: '', hr_contact: '', industry: '', website: '',
})

// Flags a client-side mismatch between the two password fields.
const passwordMismatch = computed(() => confirmPassword.value.length > 0 && confirmPassword.value !== form.password)

// Submits the registration form and routes back to login on success.
async function onSubmit() {
  errorMessage.value = ''
  successMessage.value = ''
  submitting.value = true
  try {
    await api.post('/auth/register/company', form)
    successMessage.value = 'Registration submitted. Redirecting to login…'
    setTimeout(() => router.push('/login'), 1200)
  } catch (err) {
    errorMessage.value = err.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
