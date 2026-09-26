import type { SequenceDraft, SequenceDraftClip, SequenceTransition } from "../../api/studioContracts"
import { sequenceCopy } from "./sequenceCopy"

export const TRANSITION_CYCLE: SequenceTransition[] = ["cut", "crossfade", "fade_black"]

export const CLIP_SECONDS = 5
export const DEFAULT_CLIP_DURATION_MS = CLIP_SECONDS * 1000
export const TRANSITION_SECONDS = 0.5
export const ASPECT_TOLERANCE = 0.02
export const TRIM_STEP_MS = 500
export const MIN_TRIMMED_MS = 1000

// Clamp a trim so start stays in-bounds, end stays in-bounds, and the gap is at least 1 s.
export function clampTrim(
  durationMs: number, trimStartMs: number, trimEndMs: number,
): { trimStartMs: number; trimEndMs: number } {
  const maxStart = Math.max(0, durationMs - MIN_TRIMMED_MS)
  const start = Math.min(Math.max(0, trimStartMs), maxStart)
  const end = Math.min(Math.max(start + MIN_TRIMMED_MS, trimEndMs), durationMs)
  return { trimStartMs: start, trimEndMs: end }
}

export function formatTrimPoint(ms: number): string {
  const totalTenths = Math.round(ms / 100)
  const seconds = Math.floor(totalTenths / 10)
  const tenths = totalTenths % 10
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}.${tenths}`
}

export function formatTrimRange(trimStartMs: number, trimEndMs: number): string {
  return `${formatTrimPoint(trimStartMs)}–${formatTrimPoint(trimEndMs)}`
}

const TRANSITION_INDEX = new Map(TRANSITION_CYCLE.map((transition, index) => [transition, index]))

// The chip cycles cut → crossfade → fade_black → cut.
export function nextTransition(current: SequenceTransition): SequenceTransition {
  const index = TRANSITION_INDEX.get(current) ?? 0
  return TRANSITION_CYCLE[(index + 1) % TRANSITION_CYCLE.length]
}

// Sum of each clip's trimmed length, minus 0.5 s for each non-cut transition after the first.
export function approximateTotalSeconds(draft: SequenceDraft): number {
  const trimmedSeconds = draft.clips.reduce(
    (total, clip) => total + (clip.trimEndMs - clip.trimStartMs) / 1000,
    0,
  )
  const nonCut = draft.clips.filter(
    (clip, index) => index > 0 && clip.transitionIn !== "cut",
  ).length
  return Math.max(0, trimmedSeconds - nonCut * TRANSITION_SECONDS)
}

export function formatTotal(seconds: number): string {
  const whole = Math.round(seconds)
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`
}

export function formatAspect(aspect: number): string {
  const known: [number, string][] = [
    [16 / 9, "16:9"],
    [9 / 16, "9:16"],
    [1, "1:1"],
    [4 / 5, "4:5"],
    [3 / 2, "3:2"],
  ]
  const match = known.find(([value]) => Math.abs(value - aspect) < 0.01)
  return match ? match[1] : aspect.toFixed(2)
}

export type ClipEligibility = {
  eligible: boolean
  reason: string | null
}

// AC-13: succeeded videos only; after the first clip the aspect must match.
export function clipEligibility(
  item: { kind: string; status: string; video_url: string | null; id: string },
  firstAspect: number | null,
  aspect: number | null,
  isAlreadyInDraft: boolean,
): ClipEligibility {
  if (item.kind !== "video" || item.status !== "succeeded" || !item.video_url) {
    return { eligible: false, reason: "Only finished clips can join." }
  }
  if (isAlreadyInDraft) return { eligible: true, reason: null }
  if (firstAspect !== null && aspect !== null && Math.abs(aspect - firstAspect) > ASPECT_TOLERANCE) {
    return { eligible: false, reason: sequenceCopy.picker.differentShape(formatAspect(aspect)) }
  }
  return { eligible: true, reason: null }
}

export type RenderBlocker = "need-two-clips" | "music-uploading" | null

export function renderBlocker(
  draft: SequenceDraft,
  isMusicUploading: boolean,
): RenderBlocker {
  if (draft.clips.length < 2) return "need-two-clips"
  if (isMusicUploading) return "music-uploading"
  return null
}

export function renderReason(blocker: RenderBlocker): string | null {
  if (blocker === "need-two-clips") return sequenceCopy.render.needTwoClips
  if (blocker === "music-uploading") return sequenceCopy.render.uploading
  return null
}

export type SequenceClipPayload = SequenceDraftClip["transitionIn"] extends never ? never : {
  job_id: string
  transition_in: SequenceTransition
  trim_start_ms: number
  trim_end_ms: number | null
}

// Server stores clips[0] as cut regardless, so the payload says cut there too.
// trim_end_ms is null when the clip is untrimmed at its full known length.
export function toPayloadClips(draft: SequenceDraft): SequenceClipPayload[] {
  return draft.clips.map((clip, index) => ({
    job_id: clip.jobId,
    transition_in: index === 0 ? "cut" : clip.transitionIn,
    trim_start_ms: clip.trimStartMs,
    trim_end_ms: clip.trimEndMs === clip.durationMs && clip.trimStartMs === 0 ? null : clip.trimEndMs,
  }))
}
