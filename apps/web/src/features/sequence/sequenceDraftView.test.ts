import { describe, expect, it } from "vitest"
import {
  approximateTotalSeconds,
  clipEligibility,
  formatAspect,
  formatTotal,
  nextTransition,
  renderBlocker,
  renderReason,
  toPayloadClips,
  TRANSITION_CYCLE,
} from "./sequenceDraftView"
import { EMPTY_DRAFT } from "../studio/draftOps"
import type { SequenceDraft } from "../../api/studioContracts"

function draftOf(transitions: ("cut" | "crossfade" | "fade_black")[]): SequenceDraft {
  return {
    clips: transitions.map((transitionIn, index) => ({
      jobId: `job-${index}`,
      posterUrl: null,
      aspect: null,
      transitionIn,
    })),
    audio: null,
  }
}

describe("transition chip cycling", () => {
  it("cycles cut → crossfade → fade_black → cut", () => {
    expect(TRANSITION_CYCLE).toEqual(["cut", "crossfade", "fade_black"])
    expect(nextTransition("cut")).toBe("crossfade")
    expect(nextTransition("crossfade")).toBe("fade_black")
    expect(nextTransition("fade_black")).toBe("cut")
  })
})

describe("approximate total", () => {
  it("is 5 s per clip minus 0.5 s per non-cut transition", () => {
    expect(approximateTotalSeconds(EMPTY_DRAFT)).toBe(0)
    expect(approximateTotalSeconds(draftOf(["cut", "cut"]))).toBe(10)
    expect(approximateTotalSeconds(draftOf(["cut", "crossfade", "fade_black"]))).toBe(14)
    expect(formatTotal(approximateTotalSeconds(draftOf(["cut", "crossfade", "fade_black"])))).toBe("0:14")
  })
})

describe("aspect eligibility", () => {
  const clip = { kind: "video", status: "succeeded", video_url: "/v.mp4", id: "job-1" }

  it("accepts a matching aspect", () => {
    expect(clipEligibility(clip, 16 / 9, 16 / 9, false).eligible).toBe(true)
  })

  it("disables a different aspect with its reason", () => {
    const result = clipEligibility(clip, 16 / 9, 9 / 16, false)
    expect(result.eligible).toBe(false)
    expect(result.reason).toBe("Different shape: 9:16")
  })

  it("rejects non-videos, unfinished jobs and missing urls", () => {
    expect(clipEligibility({ ...clip, kind: "image" }, null, null, false).eligible).toBe(false)
    expect(clipEligibility({ ...clip, status: "running" }, null, null, false).eligible).toBe(false)
    expect(clipEligibility({ ...clip, video_url: null }, null, null, false).eligible).toBe(false)
  })
})

describe("render blockers", () => {
  it("needs two clips", () => {
    expect(renderBlocker(draftOf(["cut"]), false)).toBe("need-two-clips")
    expect(renderReason("need-two-clips")).toBe("Add one more clip to render.")
  })
  it("waits for the music upload", () => {
    expect(renderBlocker(draftOf(["cut", "cut"]), true)).toBe("music-uploading")
    expect(renderBlocker(draftOf(["cut", "cut"]), false)).toBeNull()
  })
})

describe("payload clips", () => {
  it("forces the first transition to cut", () => {
    expect(toPayloadClips(draftOf(["crossfade", "fade_black", "cut"]))).toEqual([
      { job_id: "job-0", transition_in: "cut", trim_start_ms: 0, trim_end_ms: null },
      { job_id: "job-1", transition_in: "fade_black", trim_start_ms: 0, trim_end_ms: null },
      { job_id: "job-2", transition_in: "cut", trim_start_ms: 0, trim_end_ms: null },
    ])
  })
})

describe("formatAspect", () => {
  it("formats common ratios simply", () => {
    expect(formatAspect(16 / 9)).toBe("16:9")
    expect(formatAspect(9 / 16)).toBe("9:16")
    expect(formatAspect(1.78)).toBe("16:9")
  })
})
