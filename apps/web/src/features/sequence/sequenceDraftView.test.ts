import { describe, expect, it } from "vitest"
import {
  approximateTotalSeconds,
  clampTrim,
  clipEligibility,
  formatAspect,
  formatTotal,
  formatTrimRange,
  nextTransition,
  renderBlocker,
  renderReason,
  toPayloadClips,
  TRANSITION_CYCLE,
} from "./sequenceDraftView"
import { EMPTY_DRAFT } from "../studio/draftOps"
import type { SequenceDraft } from "../../api/studioContracts"

function draftOf(
  transitions: ("cut" | "crossfade" | "fade_black")[],
  durationMs = 5000,
): SequenceDraft {
  return {
    clips: transitions.map((transitionIn, index) => ({
      jobId: `job-${index}`,
      posterUrl: null,
      aspect: null,
      transitionIn,
      durationMs,
      trimStartMs: 0,
      trimEndMs: durationMs,
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

  it("sends trim fields when a clip is trimmed", () => {
    const draft = draftOf(["cut", "crossfade"])
    draft.clips[1] = { ...draft.clips[1], trimStartMs: 500, trimEndMs: 4000 }
    expect(toPayloadClips(draft)).toEqual([
      { job_id: "job-0", transition_in: "cut", trim_start_ms: 0, trim_end_ms: null },
      { job_id: "job-1", transition_in: "crossfade", trim_start_ms: 500, trim_end_ms: 4000 },
    ])
  })
})

describe("clampTrim", () => {
  it("keeps at least the minimum 1 s and stays in bounds", () => {
    expect(clampTrim(5000, 0, 5000)).toEqual({ trimStartMs: 0, trimEndMs: 5000 })
    expect(clampTrim(5000, -200, 5000)).toEqual({ trimStartMs: 0, trimEndMs: 5000 })
    expect(clampTrim(5000, 4800, 5000)).toEqual({ trimStartMs: 4000, trimEndMs: 5000 })
    expect(clampTrim(5000, 1000, 1200)).toEqual({ trimStartMs: 1000, trimEndMs: 2000 })
    expect(clampTrim(5000, 0, 9000)).toEqual({ trimStartMs: 0, trimEndMs: 5000 })
  })
})

describe("total length with trims", () => {
  it("uses the trimmed length, not the full clip length", () => {
    const draft = draftOf(["cut", "crossfade"])
    draft.clips[1] = { ...draft.clips[1], trimStartMs: 500, trimEndMs: 2500 }
    expect(approximateTotalSeconds(draft)).toBe(5 + 2 - 0.5)
  })
})

describe("formatTrimRange", () => {
  it("formats a mono in/out readout", () => {
    expect(formatTrimRange(500, 4000)).toBe("0:00.5–0:04.0")
    expect(formatTrimRange(0, 65000)).toBe("0:00.0–1:05.0")
  })
})

describe("formatAspect", () => {
  it("formats common ratios simply", () => {
    expect(formatAspect(16 / 9)).toBe("16:9")
    expect(formatAspect(9 / 16)).toBe("9:16")
    expect(formatAspect(1.78)).toBe("16:9")
  })
})
