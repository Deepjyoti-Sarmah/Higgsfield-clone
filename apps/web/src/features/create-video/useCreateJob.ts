import { useCallback, useRef, useState } from "react"
import type { Dispatch, SetStateAction } from "react"
import { apiClient } from "../../api/client"
import type {
  InsufficientCredits,
  JobDraft,
  RunWithGuestSession,
  SubmitErrorKind,
  SubmitState,
} from "./createVideoTypes"

export type CreateJobCallbacks = {
  onAccepted(jobId: string, draft: JobDraft): void
  onInsufficient(insufficient: InsufficientCredits): void
}

export type CreateJobControls = {
  state: SubmitState
  submitJob(draft: JobDraft): void
  retrySubmit(): void
  resetSubmit(): void
}

type Submission = { draft: JobDraft; idempotencyKey: string }
type JobPostResult =
  | { kind: "accepted"; jobId: string }
  | { kind: "insufficient"; insufficient: InsufficientCredits }
  | { kind: "error"; errorKind: SubmitErrorKind }

function trimmedPrompt(prompt: string | null): string | null {
  const trimmed = prompt?.trim() ?? ""
  return trimmed === "" ? null : trimmed
}

function submitErrorKind(status: number): SubmitErrorKind {
  if (status === 401) return "session"
  if (status === 404) return "input-missing"
  if (status === 409) return "input-not-ready"
  if (status === 422) return "invalid"
  return "network"
}

function readInsufficient(error: unknown): InsufficientCredits {
  if (typeof error === "object" && error !== null && "balance" in error && "required" in error) {
    return error as InsufficientCredits
  }
  return { detail: "", balance: 0, required: 0 }
}

async function postJob(run: RunWithGuestSession, submission: Submission): Promise<JobPostResult> {
  const { draft, idempotencyKey } = submission
  const body = {
    preset_slug: draft.presetSlug,
    input_asset_id: draft.inputAssetId,
    prompt: trimmedPrompt(draft.prompt),
    idempotency_key: idempotencyKey,
  }
  try {
    const outcome = await run(() => apiClient.POST("/api/v1/jobs", { body }))
    if (outcome.outcome === "session-failed") return { kind: "error", errorKind: "session" }
    const { response, data, error } = outcome.result
    if (response.status === 202 && data) return { kind: "accepted", jobId: data.id }
    if (response.status === 402) {
      return { kind: "insufficient", insufficient: readInsufficient(error) }
    }
    return { kind: "error", errorKind: submitErrorKind(response.status) }
  } catch {
    return { kind: "error", errorKind: "network" }
  }
}

function useSubmissionRefs() {
  const [state, setState] = useState<SubmitState>({ status: "idle" })
  const submissionRef = useRef<Submission | null>(null)
  const isSubmittingRef = useRef(false)
  return { state, setState, submissionRef, isSubmittingRef }
}

type SubmissionRefs = ReturnType<typeof useSubmissionRefs>

function useSubmitActions(
  refs: SubmissionRefs,
  runSubmission: (submission: Submission) => Promise<void>,
) {
  const { setState, submissionRef, isSubmittingRef } = refs
  const submitJob = useCallback(
    (draft: JobDraft) => {
      if (isSubmittingRef.current) return
      const submission = { draft, idempotencyKey: crypto.randomUUID() }
      submissionRef.current = submission
      isSubmittingRef.current = true
      void runSubmission(submission)
    },
    [runSubmission, submissionRef, isSubmittingRef],
  )
  const retrySubmit = useCallback(() => {
    const submission = submissionRef.current
    if (submission === null || isSubmittingRef.current) return
    isSubmittingRef.current = true
    void runSubmission(submission)
  }, [runSubmission, submissionRef, isSubmittingRef])
  const resetSubmit = useCallback(() => {
    submissionRef.current = null
    isSubmittingRef.current = false
    setState({ status: "idle" })
  }, [setState, submissionRef, isSubmittingRef])
  return { submitJob, retrySubmit, resetSubmit }
}

function applyResult(
  result: JobPostResult,
  submission: Submission,
  setState: Dispatch<SetStateAction<SubmitState>>,
  callbacks: CreateJobCallbacks,
): void {
  if (result.kind === "accepted") {
    setState({ status: "accepted", jobId: result.jobId })
    callbacks.onAccepted(result.jobId, submission.draft)
    return
  }
  if (result.kind === "insufficient") {
    setState({ status: "insufficient-credits", insufficient: result.insufficient })
    callbacks.onInsufficient(result.insufficient)
    return
  }
  setState({ status: "error", errorKind: result.errorKind, draft: submission.draft })
}

export function useCreateJob(
  runWithGuestSession: RunWithGuestSession,
  callbacks: CreateJobCallbacks,
): CreateJobControls {
  const refs = useSubmissionRefs()
  const callbacksRef = useRef(callbacks)
  callbacksRef.current = callbacks
  const runSubmission = useCallback(
    async (submission: Submission) => {
      refs.setState({ status: "submitting", draft: submission.draft })
      const result = await postJob(runWithGuestSession, submission)
      refs.isSubmittingRef.current = false
      applyResult(result, submission, refs.setState, callbacksRef.current)
    },
    [runWithGuestSession, refs],
  )
  const actions = useSubmitActions(refs, runSubmission)
  return { state: refs.state, ...actions }
}
