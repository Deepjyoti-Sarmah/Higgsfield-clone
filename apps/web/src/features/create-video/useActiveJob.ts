import { useCallback, useEffect, useRef, useState } from "react"
import { isTerminalJobStatus } from "./canvasPhase"
import type {
  ImageUploadControls,
  InsufficientCredits,
  JobDraft,
  JobWatch,
  PresetSelection,
  RunWithGuestSession,
} from "./createVideoTypes"
import { useCreateJob } from "./useCreateJob"
import type { CreateJobControls } from "./useCreateJob"
import type { CreditsControls } from "./useCredits"
import { useJobEvents } from "./useJobEvents"
import type { SessionHistory } from "./useSessionHistory"

export type ActiveJob = {
  activeJobId: string | null
  submittedAtIso: string | null
  watch: JobWatch
  startJob(draft: JobDraft): void
  openHistoryEntry(jobId: string): void
  makeAnother(): void
  retryFailedJob(): void
  dismissMissing(): void
}

// CreateJobControls ships alongside ActiveJob: the panel reads submit state directly.
export type ActiveJobControls = ActiveJob & { createJob: CreateJobControls }

export type ActiveJobDeps = {
  run: RunWithGuestSession
  history: SessionHistory
  credits: CreditsControls
  upload: ImageUploadControls
  selection: PresetSelection
}

function useAcceptHandlers(
  history: SessionHistory,
  credits: CreditsControls,
  setActiveJobId: (jobId: string | null) => void,
) {
  const { recordJob } = history
  const { refreshCredits, applyKnownBalance } = credits
  const handleJobAccepted = useCallback(
    (jobId: string, draft: JobDraft) => {
      setActiveJobId(jobId)
      recordJob({
        jobId,
        presetName: draft.presetName,
        status: "queued",
        thumbnailUrl: null,
        createdAt: new Date().toISOString(),
      })
      void refreshCredits()
    },
    [recordJob, refreshCredits, setActiveJobId],
  )
  const handleInsufficient = useCallback(
    (insufficient: InsufficientCredits) => applyKnownBalance(insufficient.balance),
    [applyKnownBalance],
  )
  return { handleJobAccepted, handleInsufficient }
}

function useWatchSync(
  watch: JobWatch,
  history: SessionHistory,
  credits: CreditsControls,
  activeJobId: string | null,
): void {
  const refreshedJobRef = useRef<string | null>(null)
  const { updateJob, removeJob } = history
  const { refreshCredits } = credits

  useEffect(() => {
    const job = watch.job
    if (job === null) return
    updateJob(job.id, {
      status: watch.status ?? job.status,
      thumbnailUrl: job.poster_url ?? job.input_image_url,
    })
  }, [watch.job, watch.status, updateJob])

  useEffect(() => {
    const job = watch.job
    const status = watch.status ?? job?.status ?? null
    if (job === null || status === null || !isTerminalJobStatus(status)) return
    if (refreshedJobRef.current === job.id) return
    refreshedJobRef.current = job.id
    void refreshCredits()
  }, [watch.job, watch.status, refreshCredits])

  useEffect(() => {
    if (watch.isMissing && activeJobId !== null) removeJob(activeJobId)
  }, [watch.isMissing, activeJobId, removeJob])
}

type JobActionsDeps = {
  watch: JobWatch
  submitJob: (draft: JobDraft) => void
  resetSubmit: () => void
  clearPreset: () => void
  setActiveJobId: (jobId: string | null) => void
  setSubmittedAtIso: (iso: string | null) => void
}

function useJobActions(deps: JobActionsDeps) {
  const { watch, submitJob, resetSubmit, clearPreset, setActiveJobId, setSubmittedAtIso } = deps
  const startJob = useCallback(
    (draft: JobDraft) => {
      setActiveJobId(null)
      setSubmittedAtIso(new Date().toISOString())
      submitJob(draft)
    },
    [submitJob, setActiveJobId, setSubmittedAtIso],
  )
  const openHistoryEntry = useCallback(
    (jobId: string) => {
      setActiveJobId(jobId)
      setSubmittedAtIso(null)
      resetSubmit()
    },
    [resetSubmit, setActiveJobId, setSubmittedAtIso],
  )
  const makeAnother = useCallback(() => {
    setActiveJobId(null)
    clearPreset()
    resetSubmit()
  }, [clearPreset, resetSubmit, setActiveJobId])
  const retryFailedJob = useCallback(() => {
    const job = watch.job
    if (job === null || job.status !== "failed") return
    startJob({
      presetSlug: job.preset_slug,
      presetName: job.preset_name,
      inputAssetId: job.input_asset_id,
      prompt: job.prompt,
    })
  }, [watch.job, startJob])
  const dismissMissing = useCallback(() => setActiveJobId(null), [setActiveJobId])
  return { startJob, openHistoryEntry, makeAnother, retryFailedJob, dismissMissing }
}

export function useActiveJob(deps: ActiveJobDeps): ActiveJobControls {
  const { run, history, credits, selection } = deps
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [submittedAtIso, setSubmittedAtIso] = useState<string | null>(null)
  const { clearPreset } = selection
  const acceptHandlers = useAcceptHandlers(history, credits, setActiveJobId)
  const createJob = useCreateJob(run, {
    onAccepted: acceptHandlers.handleJobAccepted,
    onInsufficient: acceptHandlers.handleInsufficient,
  })
  const watch = useJobEvents(activeJobId)
  useWatchSync(watch, history, credits, activeJobId)
  const actions = useJobActions({
    watch,
    submitJob: createJob.submitJob,
    resetSubmit: createJob.resetSubmit,
    clearPreset,
    setActiveJobId,
    setSubmittedAtIso,
  })

  return { activeJobId, submittedAtIso, watch, ...actions, createJob }
}
