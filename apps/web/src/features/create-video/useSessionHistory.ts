import { useCallback, useEffect, useRef, useState } from "react"
import type { HistoryEntry } from "./createVideoTypes"
import { readHistory, upsertHistoryEntry, writeHistory } from "./sessionHistoryStore"
import type { HistoryStorage } from "./sessionHistoryStore"

export type SessionHistory = {
  entries: HistoryEntry[]
  recordJob: (entry: HistoryEntry) => void
  updateJob: (
    jobId: string,
    patch: Partial<Pick<HistoryEntry, "status" | "thumbnailUrl">>,
  ) => void
  removeJob: (jobId: string) => void
}

type HistoryPatch = Partial<Pick<HistoryEntry, "status" | "thumbnailUrl">>

function browserStorage(): HistoryStorage | null {
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

function initialEntries(): HistoryEntry[] {
  const storage = browserStorage()
  return storage ? readHistory(storage) : []
}

export function useSessionHistory(): SessionHistory {
  const storageRef = useRef<HistoryStorage | null>(null)
  const [entries, setEntries] = useState<HistoryEntry[]>(initialEntries)

  useEffect(() => {
    storageRef.current = browserStorage()
  }, [])

  const changeEntries = (update: (current: HistoryEntry[]) => HistoryEntry[]) =>
    setEntries((current) => {
      const next = update(current)
      if (storageRef.current) writeHistory(storageRef.current, next)
      return next
    })

  const recordJob = useCallback((entry: HistoryEntry) => {
    changeEntries((current) => upsertHistoryEntry(current, entry))
  }, [])

  const updateJob = useCallback((jobId: string, patch: HistoryPatch) => {
    changeEntries((current) =>
      current.map((entry) => (entry.jobId === jobId ? { ...entry, ...patch } : entry)),
    )
  }, [])

  const removeJob = useCallback((jobId: string) => {
    changeEntries((current) => current.filter((entry) => entry.jobId !== jobId))
  }, [])

  return { entries, recordJob, updateJob, removeJob }
}
