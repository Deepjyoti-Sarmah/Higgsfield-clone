import { useCallback, useEffect, useRef, useState } from "react"
import type {
  WatcherDeps,
} from "./jobStatusWatcher"
import { createJobStatusWatcher } from "./jobStatusWatcher"
import { useGuestSessionRunner } from "./guestSession"
import type { GuestSessionSource, RunWithGuestSession } from "./guestSession"
import type {
  ImageInsufficient,
  ImageJob,
  ImageJobSettings,
  ImageJobSubmitError,
} from "./imageJobHelpers"
import {
  fetchImageJob,
  postImageJob,
} from "./imageJobHelpers"

export type {
  ImageInsufficient,
  ImageJob,
  ImageJobSettings,
  ImageJobSubmitError,
} from "./imageJobHelpers"

export type ImageJobPhase =
  | "idle"
  | "submitting"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "missing"

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
