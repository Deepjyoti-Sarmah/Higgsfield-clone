import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"
import { useGuestSessionRunner } from "./guestSession"
import type { GuestSessionSource, RunWithGuestSession } from "./guestSession"
import { createJobStatusWatcher } from "./jobStatusWatcher"
import type { FetchJobResult, WatcherDeps } from "./jobStatusWatcher"

export type ImageJob = components["schemas"]["ImageJobResponse"]
type ImageJobRequest = components["schemas"]["ImageJobCreateRequest"]

export type ImageJobSettings = {
  prompt: string
  aspect_ratio: ImageJobRequest["aspect_ratio"]
  quality: ImageJobRequest["quality"]
  count: number
}

export type ImageJobPhase =
  "idle" | "submitting" | "queued" | "running" | "succeeded" | "failed" | "missing"
export type ImageJobSubmitError = "network" | "session" | "invalid"
export type ImageInsufficient = { balance: number; required: number }

export type ImageJobControls = {
  phase: ImageJobPhase
  job: ImageJob | null
  creditCost: number | null
  insufficient: ImageInsufficient | null
  submitError: ImageJobSubmitError | null
  submit: (settings: ImageJobSettings) => void
  resetSubmit: () => void
  retryRead: () => void
}

type SubmitOutcome =
  | { kind: "accepted"; jobId: string; creditCost: number }
  | { kind: "insufficient"; insufficient: ImageInsufficient }
  | { kind: "error"; errorKind: ImageJobSubmitError }

function readInsufficient(error: unknown): ImageInsufficient {
  const body = (error ?? {}) as Partial<ImageInsufficient>
  return { balance: body.balance ?? 0, required: body.required ?? 0 }
}

function submitErrorKind(status: number): ImageJobSubmitError {
  if (status === 401) return "session"
  if (status === 422) return "invalid"
  return "network"
}

async function postImageJob(
  run: RunWithGuestSession,
  settings: ImageJobSettings,
  idempotencyKey: string,
): Promise<SubmitOutcome> {
  const body: ImageJobRequest = { ...settings, idempotency_key: idempotencyKey }
  try {
    const outcome = await run(() => apiClient.POST("/api/v1/image-jobs", { body }))
    if (outcome.outcome === "session-failed") return { kind: "error", errorKind: "session" }
    const { data, response, error } = outcome.result
    if (response.status === 202 && data) {
      return { kind: "accepted", jobId: data.id, creditCost: data.credit_cost }
    }
    if (response.status === 402) {
      return { kind: "insufficient", insufficient: readInsufficient(error) }
    }
    return { kind: "error", errorKind: submitErrorKind(response.status) }
  } catch {
    return { kind: "error", errorKind: "network" }
  }
}

async function fetchImageJob(jobId: string): Promise<FetchJobResult<ImageJob>> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/image-jobs/{job_id}", {
      params: { path: { job_id: jobId } },
    })
    if (response.status === 200 && data) return { kind: "ok", job: data }
    if (response.status === 401 || response.status === 404) return { kind: "missing" }
    return { kind: "network" }
  } catch {
    return { kind: "network" }
  }
}

const watcherDeps: WatcherDeps<ImageJob> = {
  openEventSource: (url: string) => new EventSource(url),
  fetchJob: fetchImageJob,
}

type ImageJobWatch = { job: ImageJob | null; isMissing: boolean }

function useImageJobWatch(jobId: string | null, nonce: number): ImageJobWatch {
  const [state, setState] = useState<ImageJobWatch>({ job: null, isMissing: false })
  useEffect(() => {
    setState({ job: null, isMissing: false })
    if (jobId === null) return
    const watcher = createJobStatusWatcher<ImageJob>(jobId, watcherDeps, {
      onJob: (job) => setState((current) => ({ ...current, job })),
      onStatus: () => undefined,
      onConnection: () => undefined,
      onMissing: () => setState((current) => ({ ...current, isMissing: true })),
    })
    return () => watcher.stop()
  }, [jobId, nonce])
  return state
}

type SubmitState = {
  isSubmitting: boolean
  submitError: ImageJobSubmitError | null
  insufficient: ImageInsufficient | null
  submit: (settings: ImageJobSettings) => void
  resetSubmit: () => void
}

function useImageSubmit(
  runWithGuestSession: RunWithGuestSession,
  onAccepted: (jobId: string, creditCost: number) => void,
): SubmitState {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<ImageJobSubmitError | null>(null)
  const [insufficient, setInsufficient] = useState<ImageInsufficient | null>(null)
  const isSubmittingRef = useRef(false)
  const onAcceptedRef = useRef(onAccepted)
  onAcceptedRef.current = onAccepted

  const submit = useCallback(
    (settings: ImageJobSettings) => {
      if (isSubmittingRef.current) return
      isSubmittingRef.current = true
      setIsSubmitting(true)
      setSubmitError(null)
      setInsufficient(null)
      void postImageJob(runWithGuestSession, settings, crypto.randomUUID()).then((outcome) => {
        isSubmittingRef.current = false
        setIsSubmitting(false)
        if (outcome.kind === "accepted") {
          onAcceptedRef.current(outcome.jobId, outcome.creditCost)
        } else if (outcome.kind === "insufficient") {
          setInsufficient(outcome.insufficient)
        } else {
          setSubmitError(outcome.errorKind)
        }
      })
    },
    [runWithGuestSession],
  )

  const resetSubmit = useCallback(() => {
    setSubmitError(null)
    setInsufficient(null)
  }, [])

  return { isSubmitting, submitError, insufficient, submit, resetSubmit }
}

function derivePhase(
  jobId: string | null,
  job: ImageJob | null,
  isMissing: boolean,
  isSubmitting: boolean,
): ImageJobPhase {
  if (isMissing) return "missing"
  if (jobId === null) return isSubmitting ? "submitting" : "idle"
  return job === null ? "queued" : job.status
}

export function useImageJob(session: GuestSessionSource): ImageJobControls {
  const runWithGuestSession = useGuestSessionRunner(session)
  const [jobId, setJobId] = useState<string | null>(null)
  const [creditCost, setCreditCost] = useState<number | null>(null)
  const [nonce, setNonce] = useState(0)
  const watch = useImageJobWatch(jobId, nonce)
  const onAccepted = useCallback((id: string, cost: number) => {
    setCreditCost(cost)
    setJobId(id)
  }, [])
  const submitState = useImageSubmit(runWithGuestSession, onAccepted)
  const { isSubmitting, submitError, insufficient, submit } = submitState
  const resetSubmitState = submitState.resetSubmit
  const retryRead = useCallback(() => setNonce((current) => current + 1), [])
  const resetSubmit = useCallback(() => {
    setJobId(null)
    setCreditCost(null)
    resetSubmitState()
  }, [resetSubmitState])

  return {
    phase: derivePhase(jobId, watch.job, watch.isMissing, isSubmitting),
    job: watch.job,
    creditCost,
    insufficient,
    submitError,
    submit,
    resetSubmit,
    retryRead,
  }
}
