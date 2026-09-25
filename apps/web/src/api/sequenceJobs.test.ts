import { beforeEach, describe, expect, it, vi } from "vitest"

const postSpy = vi.fn()

vi.mock("./client", () => ({
  apiClient: { POST: (...args: unknown[]) => postSpy(...args) },
}))

const { createSequenceJob, sequenceRequestBody } = await import("./sequenceJobs")

const CLIPS = [
  { job_id: "job-a", transition_in: "cut" as const },
  { job_id: "job-b", transition_in: "crossfade" as const },
]

function run() {
  return async <T extends { response: Response }>(request: () => Promise<T>) => ({
    outcome: "done" as const,
    result: await request(),
  })
}

describe("sequence request body", () => {
  it("includes audio_asset_id only when music is set", () => {
    const withAudio = sequenceRequestBody(CLIPS, "asset-1", "key-1")
    expect(withAudio).toEqual({
      clips: CLIPS,
      audio_asset_id: "asset-1",
      idempotency_key: "key-1",
    })
    const withoutAudio = sequenceRequestBody(CLIPS, null, "key-2")
    expect(withoutAudio).toEqual({
      clips: CLIPS,
      audio_asset_id: undefined,
      idempotency_key: "key-2",
    })
  })
})

describe("createSequenceJob status mapping", () => {
  beforeEach(() => {
    postSpy.mockReset()
  })

  it("returns accepted with the job id on 202", async () => {
    postSpy.mockResolvedValue({ data: { id: "seq-1" }, response: { status: 202 } })
    const outcome = await createSequenceJob(run(), sequenceRequestBody(CLIPS, null, "key-1"))
    expect(outcome).toEqual({ kind: "accepted", jobId: "seq-1" })
    expect(postSpy).toHaveBeenCalledWith("/api/v1/sequence-jobs", {
      body: { clips: CLIPS, audio_asset_id: undefined, idempotency_key: "key-1" },
    })
  })

  it("maps 402 to insufficient and 429 to limit", async () => {
    postSpy.mockResolvedValue({ data: null, response: { status: 402 } })
    expect(await createSequenceJob(run(), sequenceRequestBody(CLIPS, null, "key-1"))).toEqual({
      kind: "insufficient",
    })
    postSpy.mockResolvedValue({ data: null, response: { status: 429 } })
    expect(await createSequenceJob(run(), sequenceRequestBody(CLIPS, null, "key-1"))).toEqual({
      kind: "limit",
    })
  })

  it("maps 404 and 422 to clip-invalid", async () => {
    postSpy.mockResolvedValue({ data: null, response: { status: 404 } })
    expect(await createSequenceJob(run(), sequenceRequestBody(CLIPS, null, "key-1"))).toEqual({
      kind: "clip-invalid",
    })
    postSpy.mockResolvedValue({ data: null, response: { status: 422 } })
    expect(await createSequenceJob(run(), sequenceRequestBody(CLIPS, null, "key-1"))).toEqual({
      kind: "clip-invalid",
    })
  })
})
