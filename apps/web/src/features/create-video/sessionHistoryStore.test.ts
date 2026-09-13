import { expect, test } from "vitest"
import type { HistoryEntry } from "./createVideoTypes"
import {
  HISTORY_STORAGE_KEY,
  MAX_HISTORY_ENTRIES,
  readHistory,
  upsertHistoryEntry,
  writeHistory,
} from "./sessionHistoryStore"
import type { HistoryStorage } from "./sessionHistoryStore"

function makeEntry(jobId: string, overrides: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    jobId,
    presetName: "Dolly In",
    status: "queued",
    thumbnailUrl: null,
    createdAt: "2026-01-01T00:00:00Z",
    ...overrides,
  }
}

function makeStorage(raw: string | null): HistoryStorage {
  return {
    getItem: (key: string) => (key === HISTORY_STORAGE_KEY ? raw : null),
    setItem: () => undefined,
  }
}

test("readHistory returns [] when nothing is stored", () => {
  expect(readHistory(makeStorage(null))).toEqual([])
})

test("readHistory returns [] for invalid JSON", () => {
  expect(readHistory(makeStorage("{not json"))).toEqual([])
})

test("readHistory returns [] for a non-array value", () => {
  expect(readHistory(makeStorage('{"jobId":"a"}'))).toEqual([])
})

test("readHistory drops entries with a missing or invalid field", () => {
  const raw = JSON.stringify([
    makeEntry("keep"),
    { presetName: "No id", status: "queued", createdAt: "x" },
    makeEntry("badStatus", { status: "unknown" as HistoryEntry["status"] }),
  ])
  expect(readHistory(makeStorage(raw)).map((entry) => entry.jobId)).toEqual(["keep"])
})

test("writeHistory stores the entries under the versioned key", () => {
  const written: Array<[string, string]> = []
  const storage: HistoryStorage = {
    getItem: () => null,
    setItem: (key, value) => written.push([key, value]),
  }
  writeHistory(storage, [makeEntry("a")])
  expect(written).toEqual([[HISTORY_STORAGE_KEY, JSON.stringify([makeEntry("a")])]])
})

test("upsertHistoryEntry puts the newest entry first", () => {
  const result = upsertHistoryEntry([makeEntry("old")], makeEntry("new"))
  expect(result.map((entry) => entry.jobId)).toEqual(["new", "old"])
})

test("upsertHistoryEntry dedupes by jobId and moves it to the front", () => {
  const entries = [makeEntry("a"), makeEntry("b")]
  const result = upsertHistoryEntry(entries, makeEntry("b", { status: "succeeded" }))
  expect(result.map((entry) => entry.jobId)).toEqual(["b", "a"])
  expect(result[0]?.status).toBe("succeeded")
})

test("upsertHistoryEntry caps the list at 6 entries", () => {
  let entries: HistoryEntry[] = []
  for (let index = 0; index < 8; index += 1) {
    entries = upsertHistoryEntry(entries, makeEntry(`job-${index}`))
  }
  expect(entries).toHaveLength(MAX_HISTORY_ENTRIES)
  expect(entries.map((entry) => entry.jobId)).toEqual([
    "job-7",
    "job-6",
    "job-5",
    "job-4",
    "job-3",
    "job-2",
  ])
})

test("readHistory survives a storage whose getItem throws", () => {
  const storage: HistoryStorage = {
    getItem: () => {
      throw new Error("SecurityError")
    },
    setItem: () => undefined,
  }
  expect(readHistory(storage)).toEqual([])
})

test("writeHistory survives a storage whose setItem throws", () => {
  const storage: HistoryStorage = {
    getItem: () => null,
    setItem: () => {
      throw new Error("QuotaExceededError")
    },
  }
  expect(() => writeHistory(storage, [makeEntry("a")])).not.toThrow()
})
