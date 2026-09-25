import type { SequenceDraft, SequenceDraftClip, SequenceTransition } from "../../api/studioContracts"
import { sequenceCopy } from "./sequenceCopy"

export const TRANSITION_CYCLE: SequenceTransition[] = ["cut", "crossfade", "fade_black"]

export const CLIP_SECONDS = 5
export const TRANSITION_SECONDS = 0.5
export const ASPECT_TOLERANCE = 0.02

const TRANSITION_INDEX = new Map(TRANSITION_CYCLE.map((transition, index) => [transition, index]))

// The chip cycles cut → crossfade → fade_black → cut.
export function nextTransition(current: SequenceTransition): SequenceTransition {
  const index = TRANSITION_INDEX.get(current) ?? 0
  return TRANSITION_CYCLE[(index + 1) % TRANSITION_CYCLE.length]
}

// Approximate: 5 s per clip, minus 0.5 s for each non-cut transition after the first.
export function approximateTotalSeconds(draft: SequenceDraft): number {
  const nonCut = draft.clips.filter(
    (clip, index) => index > 0 && clip.transitionIn !== "cut",
  ).length
  return Math.max(0, draft.clips.length * CLIP_SECONDS - nonCut * TRANSITION_SECONDS)
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
}

// Server stores clips[0] as cut regardless, so the payload says cut there too.
export function toPayloadClips(draft: SequenceDraft): SequenceClipPayload[] {
  return draft.clips.map((clip, index) => ({
    job_id: clip.jobId,
    transition_in: index === 0 ? "cut" : clip.transitionIn,
  }))
}
