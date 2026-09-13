import { isTerminalJobStatus } from "./canvasPhase"
import type { Job, JobStatus, JobStatusEvent } from "./createVideoTypes"
export type EventSourceLike = {
  readyState: number
  close(): void
  addEventListener(type: "open" | "error" | "status", listener: (event: MessageEvent | Event) => void): void
}
export type FetchJobResult = { kind: "ok"; job: Job } | { kind: "missing" } | { kind: "network" }
export type WatcherTimers = Pick<typeof globalThis, "setTimeout" | "clearTimeout" | "setInterval" | "clearInterval">
export type WatcherDeps = {
  openEventSource(url: string): EventSourceLike
  fetchJob(jobId: string): Promise<FetchJobResult>
  timers?: WatcherTimers
}
export type WatcherCallbacks = {
  onJob(job: Job): void
  onStatus(status: JobStatus): void
  onConnection(connection: "live" | "polling"): void
  onMissing(): void
}
export type JobStatusWatcher = { stop(): void }
export const POLL_INTERVAL_MS = 5000
export const RECONNECT_DELAYS_MS = [3000, 6000, 12000, 24000, 30000]
const FINAL_FETCH_TRIES = 3
const CLOSED_READY_STATE = 2
type TimerId = ReturnType<typeof globalThis.setTimeout>

function parseStatus(data: unknown, jobId: string): JobStatus | null {
  if (typeof data !== "string") return null
  try {
    const frame = JSON.parse(data) as JobStatusEvent
    return frame.job_id === jobId ? frame.status : null
  } catch {
    return null
  }
}

class JobStatusWatcherRuntime {
  private source: EventSourceLike | null = null
  private pollTimer: TimerId | null = null
  private reconnectTimer: TimerId | null = null
  private finalTimer: TimerId | null = null
  private reconnectAttempt = 0
  private finalFetchTries = 0
  private isPolling = false
  private isFinalizing = false
  private isStopped = false
  private readonly jobId: string
  private readonly deps: WatcherDeps
  private readonly callbacks: WatcherCallbacks
  private readonly timers: WatcherTimers
  constructor(jobId: string, deps: WatcherDeps, callbacks: WatcherCallbacks) {
    this.jobId = jobId
    this.deps = deps
    this.callbacks = callbacks
    this.timers = deps.timers ?? globalThis
  }
  start(): void { this.openStream(); void this.loadInitialJob() }
  stop(): void {
    if (this.isStopped) return
    this.isStopped = true
    this.stopPoll()
    this.clearReconnect()
    if (this.finalTimer !== null) this.timers.clearTimeout(this.finalTimer)
    this.finalTimer = null
    this.source?.close()
    this.source = null
  }
  private stopPoll(): void {
    if (this.pollTimer !== null) this.timers.clearInterval(this.pollTimer)
    this.pollTimer = null
    this.isPolling = false
  }
  private clearReconnect(): void {
    if (this.reconnectTimer !== null) this.timers.clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
  }
  private openStream(): void {
    if (this.isStopped) return
    const next = this.deps.openEventSource(`/api/v1/jobs/${this.jobId}/events`)
    this.source = next
    next.addEventListener("open", () => this.handleOpen())
    next.addEventListener("error", () => this.handleError())
    next.addEventListener("status", (event) => this.handleStatus(event))
  }
  private handleOpen(): void {
    if (this.isStopped || this.isFinalizing) return
    this.callbacks.onConnection("live")
    this.stopPoll()
    this.reconnectAttempt = 0
  }
  private handleError(): void {
    if (this.isStopped || this.isFinalizing) return
    this.startPolling()
    if (this.source !== null && this.source.readyState === CLOSED_READY_STATE) this.scheduleReconnect()
  }
  private scheduleReconnect(): void {
    if (this.isStopped || this.reconnectTimer !== null) return
    this.source?.close()
    this.source = null
    const index = Math.min(this.reconnectAttempt, RECONNECT_DELAYS_MS.length - 1)
    this.reconnectAttempt += 1
    this.reconnectTimer = this.timers.setTimeout(() => {
      this.reconnectTimer = null
      this.openStream()
    }, RECONNECT_DELAYS_MS[index])
  }
  private startPolling(): void {
    if (this.isPolling || this.isStopped || this.isFinalizing) return
    this.isPolling = true
    this.callbacks.onConnection("polling")
    void this.poll()
    this.pollTimer = this.timers.setInterval(() => void this.poll(), POLL_INTERVAL_MS)
  }
  private handleStatus(event: MessageEvent | Event): void {
    if (this.isStopped || this.isFinalizing) return
    const status = parseStatus((event as MessageEvent).data, this.jobId)
    if (status === null) return
    this.callbacks.onStatus(status)
    if (this.isPolling) {
      this.stopPoll()
      this.callbacks.onConnection("live")
    }
    if (isTerminalJobStatus(status)) this.startFinalFetch()
  }
  private startFinalFetch(): void {
    this.isFinalizing = true
    this.clearReconnect()
    this.stopPoll()
    this.source?.close()
    this.source = null
    void this.loadFinalJob()
  }
  private async loadFinalJob(): Promise<void> {
    const result = await this.deps.fetchJob(this.jobId)
    if (this.isStopped) return
    if (result.kind !== "network") {
      if (result.kind === "ok") this.callbacks.onJob(result.job)
      this.stop()
      return
    }
    this.finalFetchTries += 1
    if (this.finalFetchTries >= FINAL_FETCH_TRIES) {
      this.stop()
      return
    }
    this.finalTimer = this.timers.setTimeout(() => void this.loadFinalJob(), POLL_INTERVAL_MS)
  }
  private handlePolledStatus(status: JobStatus): void {
    if (isTerminalJobStatus(status)) {
      this.callbacks.onStatus(status)
      this.stop()
      return
    }
    if (this.isPolling) this.callbacks.onStatus(status)
  }
  private async poll(): Promise<void> {
    const result = await this.deps.fetchJob(this.jobId)
    if (this.isStopped || this.isFinalizing) return
    if (result.kind === "missing") {
      this.callbacks.onMissing()
      this.stop()
      return
    }
    if (result.kind === "network") return
    this.callbacks.onJob(result.job)
    this.handlePolledStatus(result.job.status)
  }
  private async loadInitialJob(): Promise<void> {
    const result = await this.deps.fetchJob(this.jobId)
    if (this.isStopped) return
    if (result.kind === "missing") {
      this.callbacks.onMissing()
      this.stop()
      return
    }
    if (result.kind === "network") {
      this.startPolling()
      return
    }
    this.callbacks.onJob(result.job)
    if (isTerminalJobStatus(result.job.status)) {
      this.callbacks.onStatus(result.job.status)
      this.stop()
    }
  }
}

export function createJobStatusWatcher(
  jobId: string,
  deps: WatcherDeps,
  callbacks: WatcherCallbacks,
): JobStatusWatcher {
  const runtime = new JobStatusWatcherRuntime(jobId, deps, callbacks)
  runtime.start()
  return { stop: () => runtime.stop() }
}
