import { expect, test } from "vitest"
import { CANVAS_TRANSITIONS, deriveCanvasPhase, isTerminalJobStatus } from "./canvasPhase"
import type { CanvasPhase, JobStatus } from "./createVideoTypes"

type PhaseInput = Parameters<typeof deriveCanvasPhase>[0]

const idleInput: PhaseInput = {
  uploadStatus: "idle",
  submitStatus: "idle",
  activeJobId: null,
  jobStatus: null,
  isJobMissing: false,
}

function phase(input: Partial<PhaseInput>): CanvasPhase {
  return deriveCanvasPhase({ ...idleInput, ...input })
}

function assertJourney(inputs: PhaseInput[]): void {
  const phases = inputs.map(deriveCanvasPhase)
  phases.slice(1).forEach((to, index) => {
    const from = phases[index]
    expect(CANVAS_TRANSITIONS[from], `${from} → ${to}`).toContain(to)
  })
}

test("isTerminalJobStatus is true only for succeeded and failed", () => {
  const statuses: JobStatus[] = ["queued", "running", "succeeded", "failed"]
  expect(statuses.filter(isTerminalJobStatus)).toEqual(["succeeded", "failed"])
})

test("every phase has a transitions entry", () => {
  const allPhases: CanvasPhase[] = [
    "empty",
    "uploading",
    "ready",
    "submitting",
    "queued",
    "generating",
    "succeeded",
    "failed",
  ]
  expect(Object.keys(CANVAS_TRANSITIONS).sort()).toEqual([...allPhases].sort())
})

test("an active job outranks the upload and submit state", () => {
  const input = {
    activeJobId: "job-1",
    uploadStatus: "uploading" as const,
    submitStatus: "submitting" as const,
  }
  expect(phase({ ...input, jobStatus: "running" })).toBe("generating")
})

test("a missing job is failed even after a succeeded status", () => {
  expect(phase({ activeJobId: "job-1", jobStatus: "succeeded", isJobMissing: true })).toBe(
    "failed",
  )
})

test("job status maps to succeeded, failed, generating and queued", () => {
  expect(phase({ activeJobId: "job-1", jobStatus: "succeeded" })).toBe("succeeded")
  expect(phase({ activeJobId: "job-1", jobStatus: "failed" })).toBe("failed")
  expect(phase({ activeJobId: "job-1", jobStatus: "running" })).toBe("generating")
  expect(phase({ activeJobId: "job-1", jobStatus: "queued" })).toBe("queued")
  expect(phase({ activeJobId: "job-1", jobStatus: null })).toBe("queued")
})

test("submitting outranks the upload state when no job is active", () => {
  expect(phase({ submitStatus: "submitting", uploadStatus: "uploading" })).toBe("submitting")
})

test("upload status maps to empty, uploading and ready", () => {
  expect(phase({ uploadStatus: "idle" })).toBe("empty")
  expect(phase({ uploadStatus: "error" })).toBe("empty")
  expect(phase({ uploadStatus: "uploading" })).toBe("uploading")
  expect(phase({ uploadStatus: "ready" })).toBe("ready")
})

test("journey: drop, upload, generate, succeed, make another", () => {
  const ready: PhaseInput = { ...idleInput, uploadStatus: "ready" }
  const accepted: PhaseInput = { ...ready, submitStatus: "accepted", activeJobId: "job-1" }
  assertJourney([
    idleInput,
    { ...idleInput, uploadStatus: "uploading" },
    ready,
    { ...ready, submitStatus: "submitting" },
    { ...accepted, jobStatus: "queued" },
    { ...accepted, jobStatus: "running" },
    { ...accepted, jobStatus: "succeeded" },
    ready,
  ])
})

test("journey: a failed upload returns to empty", () => {
  assertJourney([
    idleInput,
    { ...idleInput, uploadStatus: "uploading" },
    { ...idleInput, uploadStatus: "error" },
  ])
})

test("journey: replace mid-upload and remove after ready", () => {
  assertJourney([
    idleInput,
    { ...idleInput, uploadStatus: "uploading" },
    { ...idleInput, uploadStatus: "uploading" },
    { ...idleInput, uploadStatus: "ready" },
    { ...idleInput, uploadStatus: "uploading" },
    { ...idleInput, uploadStatus: "ready" },
    idleInput,
  ])
})

test("journey: 402 returns to ready, remove while submitting goes empty", () => {
  const ready: PhaseInput = { ...idleInput, uploadStatus: "ready" }
  assertJourney([ready, { ...ready, submitStatus: "submitting" }, ready])
  assertJourney([ready, { ...ready, submitStatus: "submitting" }, idleInput])
})

test("journey: a reaper re-queue goes generating back to queued", () => {
  const accepted: PhaseInput = { ...idleInput, uploadStatus: "ready", activeJobId: "job-1" }
  assertJourney([
    { ...accepted, jobStatus: "queued" },
    { ...accepted, jobStatus: "running" },
    { ...accepted, jobStatus: "queued" },
    { ...accepted, jobStatus: "running" },
    { ...accepted, jobStatus: "failed" },
  ])
})

test("journey: generate again while a job is running", () => {
  const accepted: PhaseInput = { ...idleInput, uploadStatus: "ready", activeJobId: "job-1" }
  assertJourney([
    { ...accepted, jobStatus: "queued" },
    { ...idleInput, uploadStatus: "ready", submitStatus: "submitting" },
    { ...idleInput, uploadStatus: "ready", submitStatus: "accepted", activeJobId: "job-2", jobStatus: "queued" },
  ])
})

test("journey: a history entry opens from empty", () => {
  const ready: PhaseInput = { ...idleInput, uploadStatus: "ready", activeJobId: "job-1" }
  assertJourney([idleInput, { ...ready, jobStatus: "running" }])
  assertJourney([idleInput, { ...ready, jobStatus: "succeeded" }])
  assertJourney([idleInput, { ...ready, jobStatus: "failed" }])
})

test("journey: switching history entries while one is running", () => {
  const ready: PhaseInput = { ...idleInput, uploadStatus: "ready" }
  assertJourney([
    { ...ready, activeJobId: "job-1", jobStatus: "running" },
    { ...ready, activeJobId: "job-2", jobStatus: "succeeded" },
  ])
})

test("journey: a missing job fails and back to create returns to ready", () => {
  const ready: PhaseInput = { ...idleInput, uploadStatus: "ready", activeJobId: "job-1" }
  assertJourney([
    { ...ready, jobStatus: "running" },
    { ...ready, jobStatus: "running", isJobMissing: true },
    { ...idleInput, uploadStatus: "ready" },
  ])
})

test("journey: retry after failure and make another without an image", () => {
  const ready: PhaseInput = { ...idleInput, uploadStatus: "ready" }
  assertJourney([
    { ...ready, activeJobId: "job-1", jobStatus: "failed" },
    { ...ready, submitStatus: "submitting" },
    { ...ready, submitStatus: "accepted", activeJobId: "job-2", jobStatus: "queued" },
  ])
  assertJourney([{ ...ready, activeJobId: "job-1", jobStatus: "succeeded" }, idleInput])
})
