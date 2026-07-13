<template>
  <!-- Renders the shared login form for all three roles. -->
  <div class="pp-auth-shell">
    <div class="pp-card pp-auth-card">
      <div class="pp-auth-brand">PlacementPro</div>
      <p class="text-muted mb-4">Sign in to your account</p>

      <div v-if="errorMessage" class="alert alert-danger py-2">{{ errorMessage }}</div>

      <form novalidate @submit.prevent="onSubmit">
        <div class="mb-3">
          <label class="form-label">Email address</label>
          <input v-model.trim="form.email" type="email" class="form-control" required autocomplete="email" />
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input v-model="form.password" type="password" class="form-control" required minlength="6" autocomplete="current-password" />
        </div>
        <button type="submit" class="btn btn-primary w-100" :disabled="submitting">
          {{ submitting ? 'Signing in…' : 'Sign In' }}
        </button>
      </form>

      <div class="text-center mt-4 small">
        <span class="text-muted">New here?</span>
        <router-link to="/register/student" class="ms-1">Register as Student</router-link>
        <span class="text-muted mx-1">·</span>
        <router-link to="/register/company">Register your Company</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { setSession, homeForRole } from '@/utils/auth'

const router = useRouter()
const form = reactive({ email: '', password: '' })
const submitting = ref(false)
const errorMessage = ref('')

// Submits the login form and redirects to the resolved role home.
async function onSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    const { data } = await api.post('/auth/login', form)
    setSession(data)
    router.push(homeForRole(data.role))
  } catch (err) {
    errorMessage.value = err.response?.data?.message || 'Unable to sign in. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
