import axios from 'axios'
import { auth, clearSession } from '@/utils/auth'
import router from '@/router'

// Creates the shared axios instance pointed at the Flask API.
const api = axios.create({ baseURL: '/api' })

// Attaches the bearer token to every outgoing request.
api.interceptors.request.use((requestConfig) => {
  if (auth.token) {
    requestConfig.headers.Authorization = `Bearer ${auth.token}`
  }
  return requestConfig
})

// Clears the session and redirects to login on an expired/invalid token.
api.interceptors.response.use(
  (response) => response,
  (err) => {
    if (err.response && err.response.status === 401) {
      clearSession()
      router.push('/login')
    }
    return Promise.reject(err)
  }
)

export default api
