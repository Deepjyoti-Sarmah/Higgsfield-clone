// Mono meta durations: 0:05 style, minutes when over an hour is unnecessary here.
export function formatDuration(ms: number | null | undefined): string | null {
  if (ms === null || ms === undefined) return null
  const totalSeconds = Math.max(0, Math.round(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, "0")}`
}
