import { auth } from '@/utils/auth'

// Opens an SSE connection to the student's live application-update stream and calls
// `onUpdate(applicationId)` for each event. Returns a cleanup function that closes it.
// Meant to be opened on mount and closed on unmount by whichever view is showing live status.
export function subscribeToApplicationUpdates(onUpdate) {
  if (!auth.token) return () => {}

  const source = new EventSource(`/api/student/events?token=${encodeURIComponent(auth.token)}`)
  source.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.application_id) onUpdate(payload.application_id)
    } catch {
      // Ignores malformed/keep-alive payloads.
    }
  }
  return () => source.close()
}
