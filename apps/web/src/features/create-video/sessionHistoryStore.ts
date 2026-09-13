import type { HistoryEntry, JobStatus } from "./createVideoTypes"

export const HISTORY_STORAGE_KEY = "hf.createVideo.history.v1"
export const MAX_HISTORY_ENTRIES = 6

const jobStatuses: JobStatus[] = ["queued", "running", "succeeded", "failed"]

export type HistoryStorage = {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
}

export function isHistoryEntry(value: unknown): value is HistoryEntry {
  if (typeof value !== "object" || value === null) return false
  const entry = value as Record<string, unknown>
  const hasText =
    typeof entry.jobId === "string" &&
    typeof entry.presetName === "string" &&
    typeof entry.createdAt === "string"
  const hasThumb = typeof entry.thumbnailUrl === "string" || entry.thumbnailUrl === null
  return hasText && hasThumb && jobStatuses.includes(entry.status as JobStatus)
}

export function readHistory(storage: HistoryStorage): HistoryEntry[] {
  try {
    const raw = storage.getItem(HISTORY_STORAGE_KEY)
    if (raw === null) return []
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter(isHistoryEntry) : []
  } catch {
    return []
  }
}

export function writeHistory(storage: HistoryStorage, entries: HistoryEntry[]): void {
  try {
    storage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(entries))
  } catch {
    // private mode or quota: the hook keeps the list in memory
  }
}

export function upsertHistoryEntry(
  entries: HistoryEntry[],
  entry: HistoryEntry,
): HistoryEntry[] {
  const others = entries.filter((existing) => existing.jobId !== entry.jobId)
  return [entry, ...others].slice(0, MAX_HISTORY_ENTRIES)
}
