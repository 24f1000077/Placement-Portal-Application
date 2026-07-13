import { reactive } from 'vue'

// Reads any persisted session from local storage.
const stored = JSON.parse(localStorage.getItem('pp_auth') || 'null')

// Holds the single reactive source of truth for the logged-in user.
export const auth = reactive({
  token: stored?.token || null,
  role: stored?.role || null,
  name: stored?.name || null,
  email: stored?.email || null,
})

// Persists the given session and updates reactive state.
export function setSession(session) {
  auth.token = session.access_token
  auth.role = session.role
  auth.name = session.name
  auth.email = session.email
  localStorage.setItem('pp_auth', JSON.stringify({
    token: auth.token, role: auth.role, name: auth.name, email: auth.email,
  }))
}

// Clears the reactive state and persisted session.
export function clearSession() {
  auth.token = null
  auth.role = null
  auth.name = null
  auth.email = null
  localStorage.removeItem('pp_auth')
}

// Maps a role name to its dashboard home route path.
export function homeForRole(role) {
  if (role === 'ADMIN') return '/overview'
  if (role === 'COMPANY') return '/company/overview'
  if (role === 'STUDENT') return '/student/drives'
  return '/login'
}
