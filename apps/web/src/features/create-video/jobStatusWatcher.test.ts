import { afterEach, beforeEach, expect, test, vi } from "vitest"
import type { Job, JobStatus } from "./createVideoTypes"
import {
  POLL_INTERVAL_MS,
  RECONNECT_DELAYS_MS,
  createJobStatusWatcher,
} from "./jobStatusWatcher"
import type { EventSourceLike, FetchJobResult, WatcherDeps } from "./jobStatusWatcher"

type Listener = (event: MessageEvent | Event) => void

class FakeEventSource implements EventSourceLike {
  readyState = 0
  isClosed = false
  private readonly listeners = new Map<string, Listener[]>()

  close(): void {
    this.isClosed = true
    this.readyState = 2
  }

  addEventListener(type: "open" | "error" | "status", listener: Listener): void {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener])
  }

  emit(type: "open" | "error" | "status", event?: MessageEvent | Event): void {
    for (const listener of this.listeners.get(type) ?? []) listener(event ?? new Event(type))
  }
}

function makeJob(status: JobStatus): Job {
  return {
    id: "job-1",
    status,
    preset_slug: "dolly-in",
    preset_name: "Dolly In",
    prompt: null,
    credit_cost: 20,
    input_asset_id: "asset-1",
    input_image_url: null,
    video_url: null,
    poster_url: null,
    error_message: null,
    created_at: "2026-01-01T00:00:00Z",
    started_at: null,
    finished_at: null,
  }
}

function statusFrame(status: JobStatus, jobId = "job-1"): MessageEvent {
  return { data: JSON.stringify({ job_id: jobId, status }) } as MessageEvent
}

function makeHarness() {
  const sources: FakeEventSource[] = []
  const fetchJob = vi.fn(async (): Promise<FetchJobResult> => ({ kind: "ok", job: makeJob("queued") }))
  const deps: WatcherDeps = {
    openEventSource: () => {
      const source = new FakeEventSource()
      sources.push(source)
      return source
    },
    fetchJob,
  }
  const callbacks = {
    onJob: vi.fn(),
    onStatus: vi.fn(),
    onConnection: vi.fn(),
    onMissing: vi.fn(),
  }
  return { sources, fetchJob, deps, callbacks }
}
type Harness = ReturnType<typeof makeHarness>
const currentSource = (harness: Harness): FakeEventSource =>
  harness.sources[harness.sources.length - 1]
const flush = async (): Promise<void> => {
  await vi.advanceTimersByTimeAsync(0)
}
beforeEach(() => {
  vi.useFakeTimers()
})
afterEach(() => {
  vi.useRealTimers()
})
test("a terminal status frame closes the EventSource and fetches the final job", async () => {
  const harness = makeHarness()
  createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  currentSource(harness).emit("status", statusFrame("succeeded"))
  await flush()
  expect(currentSource(harness).isClosed).toBe(true)
  expect(harness.callbacks.onStatus).toHaveBeenCalledWith("succeeded")
})
test("an error starts a poll that repeats every 5 seconds", async () => {
  const harness = makeHarness()
  createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  expect(harness.fetchJob).toHaveBeenCalledTimes(1)
  currentSource(harness).emit("error")
  await flush()
  expect(harness.fetchJob).toHaveBeenCalledTimes(2)
  expect(harness.callbacks.onConnection).toHaveBeenLastCalledWith("polling")
  await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
  expect(harness.fetchJob).toHaveBeenCalledTimes(3)
})
test("an open event stops the poll and reports live", async () => {
  const harness = makeHarness()
  createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  currentSource(harness).emit("error")
  await flush()
  currentSource(harness).emit("open")
  expect(harness.callbacks.onConnection).toHaveBeenLastCalledWith("live")
  await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 2)
  expect(harness.fetchJob).toHaveBeenCalledTimes(2)
})
test("a closed EventSource reconnects on the backoff ladder", async () => {
  const harness = makeHarness()
  createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  for (const [index, delay] of RECONNECT_DELAYS_MS.entries()) {
    const source = currentSource(harness)
    source.readyState = 2
    source.emit("error")
    await vi.advanceTimersByTimeAsync(delay - 1)
    expect(harness.sources).toHaveLength(index + 1)
    await vi.advanceTimersByTimeAsync(1)
    expect(harness.sources).toHaveLength(index + 2)
  }
})
test("a late poll cannot override a newer live status frame", async () => {
  const harness = makeHarness()
  let resolvePoll: (result: FetchJobResult) => void = () => undefined
  harness.fetchJob.mockImplementationOnce(async () => ({ kind: "ok", job: makeJob("queued") }))
  harness.fetchJob.mockImplementationOnce(
    () => new Promise<FetchJobResult>((resolve) => {
      resolvePoll = resolve
    }),
  )
  const watcher = createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  currentSource(harness).emit("error")
  await flush()
  currentSource(harness).emit("status", statusFrame("running"))
  resolvePoll({ kind: "ok", job: makeJob("queued") })
  await flush()
  expect(harness.callbacks.onStatus).toHaveBeenCalledTimes(1)
  expect(harness.callbacks.onStatus).toHaveBeenCalledWith("running")
  watcher.stop()
})
test("an unparseable frame or a frame for another job is ignored", async () => {
  const harness = makeHarness()
  const watcher = createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  currentSource(harness).emit("status", { data: "not-json" } as MessageEvent)
  currentSource(harness).emit("status", statusFrame("failed", "other-job"))
  expect(harness.callbacks.onStatus).not.toHaveBeenCalled()
  expect(currentSource(harness).isClosed).toBe(false)
  watcher.stop()
})
test("a missing job stops the watcher", async () => {
  const harness = makeHarness()
  harness.fetchJob.mockImplementationOnce(async () => ({ kind: "ok", job: makeJob("queued") }))
  harness.fetchJob.mockImplementationOnce(async () => ({ kind: "missing" }))
  createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  currentSource(harness).emit("error")
  await flush()
  expect(harness.callbacks.onMissing).toHaveBeenCalledTimes(1)
  expect(currentSource(harness).isClosed).toBe(true)
  await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 2)
  expect(harness.fetchJob).toHaveBeenCalledTimes(2)
})
test("stop is idempotent and silences later callbacks", async () => {
  const harness = makeHarness()
  const watcher = createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  watcher.stop()
  watcher.stop()
  currentSource(harness).emit("status", statusFrame("succeeded"))
  currentSource(harness).emit("error")
  await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS)
  expect(harness.callbacks.onStatus).not.toHaveBeenCalled()
  expect(harness.callbacks.onJob).toHaveBeenCalledTimes(1)
  expect(harness.fetchJob).toHaveBeenCalledTimes(1)
  expect(currentSource(harness).isClosed).toBe(true)
})
test("a terminal initial fetch stops without waiting for an SSE frame", async () => {
  const harness = makeHarness()
  harness.fetchJob.mockImplementationOnce(async () => ({ kind: "ok", job: makeJob("succeeded") }))
  createJobStatusWatcher("job-1", harness.deps, harness.callbacks)
  await flush()
  expect(harness.callbacks.onJob).toHaveBeenCalledWith(
    expect.objectContaining({ status: "succeeded" }),
  )
  expect(harness.callbacks.onStatus).toHaveBeenCalledWith("succeeded")
  expect(harness.fetchJob).toHaveBeenCalledTimes(1)
  expect(currentSource(harness).isClosed).toBe(true)
})
