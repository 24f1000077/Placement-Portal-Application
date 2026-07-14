<template>
  <!-- Renders the student self-registration form. -->
  <div class="pp-auth-shell">
    <div class="pp-card pp-auth-card" style="max-width: 560px;">
      <div class="pp-auth-brand">PlacementPro</div>
      <p class="text-muted mb-4">Create your student account</p>

      <div v-if="errorMessage" class="alert alert-danger py-2">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success py-2">{{ successMessage }}</div>

      <form @submit.prevent="onSubmit">
        <div class="row g-3">
          <div class="col-12">
            <label class="form-label">Full Name</label>
            <input v-model.trim="form.name" type="text" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Email address</label>
            <input v-model.trim="form.email" type="email" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Contact Number</label>
            <input
              v-model="form.contact_number"
              @input="form.contact_number = form.contact_number.replace(/\D/g, '').slice(0, 15)"
              type="tel"
              inputmode="numeric"
              class="form-control"
              pattern="\d{7,15}"
              title="Digits only, 7-15 characters"
              required
            />
          </div>
          <div class="col-md-6">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control" required minlength="6" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Confirm Password</label>
            <input v-model="confirmPassword" type="password" class="form-control" required minlength="6" />
          </div>
          <div class="col-md-6">
            <label class="form-label">CGPA</label>
            <input v-model.number="form.cgpa" type="number" class="form-control" min="0" max="10" step="0.01" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Graduation Year</label>
            <input v-model.number="form.graduation_year" type="number" class="form-control" min="2020" max="2035" required />
          </div>
          <div class="col-12">
            <label class="form-label">Branch</label>
            <select v-model.number="form.branch_id" class="form-select" required>
              <option value="" disabled>Select</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>
          <div class="col-12">
            <label class="form-label">Skills</label>
            <input v-model.trim="form.skills" type="text" class="form-control" placeholder="e.g. Python, SQL, React" />
          </div>
          <div class="col-12">
            <label class="form-label">Project Experience</label>
            <textarea v-model.trim="form.experience" class="form-control" rows="3" placeholder="Briefly describe relevant projects"></textarea>
          </div>
        </div>

        <button type="submit" class="btn btn-primary w-100 mt-4" :disabled="submitting || passwordMismatch">
          {{ submitting ? 'Creating account…' : 'Register' }}
        </button>
        <div v-if="passwordMismatch" class="text-danger small mt-2">Passwords do not match.</div>
      </form>

      <div class="text-center mt-4 small">
        <span class="text-muted">Already have an account?</span>
        <router-link to="/login" class="ms-1">Sign In</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const branches = ref([])
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const confirmPassword = ref('')

const form = reactive({
  name: '', email: '', password: '', contact_number: '',
  cgpa: null, graduation_year: null, branch_id: '', skills: '', experience: '',
})

// Flags a client-side mismatch between the two password fields.
const passwordMismatch = computed(() => confirmPassword.value.length > 0 && confirmPassword.value !== form.password)

// Loads the branch list used to populate the branch dropdown.
onMounted(async () => {
  const { data } = await api.get('/auth/branches')
  branches.value = data
})

// Submits the registration form and routes back to login on success.
async function onSubmit() {
  errorMessage.value = ''
  successMessage.value = ''
  submitting.value = true
  try {
    await api.post('/auth/register/student', form)
    successMessage.value = 'Registration successful. Redirecting to login…'
    setTimeout(() => router.push('/login'), 1200)
  } catch (err) {
    errorMessage.value = err.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>
