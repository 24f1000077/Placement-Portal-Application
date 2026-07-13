import api from '@/services/api'

// Fetches a protected file through the authenticated API client and triggers a browser download.
export async function downloadFile(url, filename) {
  const res = await api.get(url, { responseType: 'blob' })
  const objectUrl = URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.click()
  URL.revokeObjectURL(objectUrl)
}
