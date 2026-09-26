import { describe, expect, it } from "vitest"
import { videoFaceSwapJobBody, videoFaceSwapOutcomeFor } from "./videoFaceswapJobs"
import { checkVideoFile, isVideoSeedUrl, videoRenderCost } from "../features/face-swap/videoFaceSwapCost"
import { progressPathFor } from "./jobProgress"

function videoFile(name: string, type: string, size: number): File {
  return new File([new Uint8Array(size)], name, { type })
}

describe("video face swap job body", () => {
  it("carries the rail job id, the face asset, the keyframe, and an idempotency key", () => {
    expect(videoFaceSwapJobBody("face-1", "job-1", "key-1", "frame-1")).toEqual({
      source_asset_id: "face-1",
      target_job_id: "job-1",
      keyframe_asset_id: "frame-1",
      idempotency_key: "key-1",
    })
  })

  it("allows a missing keyframe", () => {
    expect(videoFaceSwapJobBody("face-1", "job-1", "key-1", null).keyframe_asset_id).toBeNull()
  })
})

describe("video face swap outcome", () => {
  it("maps creation statuses like the image swap path", () => {
    expect(videoFaceSwapOutcomeFor(202, { id: "job-1" }, null)).toEqual({ kind: "accepted", jobId: "job-1" })
    expect(videoFaceSwapOutcomeFor(402, undefined, { balance: 1, required: 10 }).kind).toBe("insufficient")
    expect(videoFaceSwapOutcomeFor(429, undefined, null)).toEqual({ kind: "limit" })
    expect(videoFaceSwapOutcomeFor(422, undefined, null)).toEqual({ kind: "invalid" })
    expect(videoFaceSwapOutcomeFor(500, undefined, null)).toEqual({ kind: "error" })
  })
})

describe("video render cost", () => {
  it("charges ceil(duration_s) x 2 credits", () => {
    expect(videoRenderCost(5000)).toBe(10)
    expect(videoRenderCost(5100)).toBe(12)
    expect(videoRenderCost(30000)).toBe(60)
    expect(videoRenderCost(null)).toBeNull()
  })
})

describe("video target checks", () => {
  it("accepts mp4 files within 50 MB", () => {
    expect(checkVideoFile(videoFile("clip.mp4", "video/mp4", 100))).toBeNull()
  })

  it("rejects non-mp4 and oversize files", () => {
    expect(checkVideoFile(videoFile("clip.png", "image/png", 100))).toBe("invalid-type")
    expect(checkVideoFile(videoFile("clip.mp4", "video/mp4", 50_000_001))).toBe("too-big")
  })

  it("routes rail seeds to the video well by extension", () => {
    expect(isVideoSeedUrl("https://cdn.example/jobs/abc/video.mp4")).toBe(true)
    expect(isVideoSeedUrl("https://cdn.example/jobs/abc/image-1.png")).toBe(false)
  })
})

describe("video faceswap progress path", () => {
  it("polls the video-faceswap job endpoint", () => {
    expect(progressPathFor("video_faceswap")).toBe("/api/v1/video-faceswap-jobs/{job_id}")
  })
})
