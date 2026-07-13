// Formats an ISO date string as dd/mm/yyyy.
export function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  return `${dd}/${mm}/${d.getFullYear()}`
}

// Formats an ISO date string as dd/mm/yyyy, HH:mm.
export function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${formatDate(iso)}, ${hh}:${min}`
}

// Returns the current local time formatted for a datetime-local input's min attribute.
export function nowForDateTimeLocal() {
  const d = new Date(Date.now() + 60000)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// Returns today's local date formatted for a date input's min attribute.
export function todayForDateInput() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
