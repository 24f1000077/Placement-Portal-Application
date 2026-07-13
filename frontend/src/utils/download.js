import api from '@/services/api'

// Builds a filename like "jane_doe_resume.pdf" from a student's display name and a suffix.
export function studentFileName(studentName, suffix) {
  const safe = (studentName || 'student').trim().replace(/\s+/g, '_')
  return `${safe}_${suffix}`
}

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
