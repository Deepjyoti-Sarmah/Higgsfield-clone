import type { SequenceDraft, SequenceDraftClip, SequenceTransition } from "../../api/studioContracts"

export const MAX_SEQUENCE_CLIPS = 6

export const EMPTY_DRAFT: SequenceDraft = { clips: [], audio: null }

// Pure draft operations so the rules can be unit-tested without a DOM.
export function addClipToDraft(
  draft: SequenceDraft,
  clip: Omit<SequenceDraftClip, "transitionIn" | "trimStartMs" | "trimEndMs">,
): SequenceDraft | null {
  if (draft.clips.length >= MAX_SEQUENCE_CLIPS) return null
  // The first clip's transition is always a hard cut. Untrimmed spans the full known length.
  const transitionIn: SequenceTransition = draft.clips.length === 0 ? "cut" : "crossfade"
  const newClip = { ...clip, transitionIn, trimStartMs: 0, trimEndMs: clip.durationMs }
  return { ...draft, clips: [...draft.clips, newClip] }
}

export function removeClipFromDraft(draft: SequenceDraft, index: number): SequenceDraft {
  return { ...draft, clips: draft.clips.filter((_, at) => at !== index) }
}

export function moveClipWithinDraft(draft: SequenceDraft, from: number, to: number): SequenceDraft {
  const clips = [...draft.clips]
  const [moved] = clips.splice(from, 1)
  clips.splice(to, 0, moved)
  return { ...draft, clips }
}

export function setClipTransition(
  draft: SequenceDraft, index: number, transition: SequenceDraftClip["transitionIn"],
): SequenceDraft {
  return {
    ...draft,
    clips: draft.clips.map((clip, at) =>
      at === 0 || at !== index ? clip : { ...clip, transitionIn: transition }),
  }
}

export function setClipTrim(
  draft: SequenceDraft, index: number, trimStartMs: number, trimEndMs: number,
): SequenceDraft {
  return {
    ...draft,
    clips: draft.clips.map((clip, at) =>
      at !== index ? clip : { ...clip, trimStartMs, trimEndMs }),
  }
}

export function readStoredDraft(): SequenceDraft {
  try {
    const raw = sessionStorage.getItem("reel-still.sequence-draft")
    if (raw === null) return EMPTY_DRAFT
    const parsed = JSON.parse(raw) as SequenceDraft
    return Array.isArray(parsed.clips) ? parsed : EMPTY_DRAFT
  } catch {
    return EMPTY_DRAFT
  }
}

export function writeStoredDraft(draft: SequenceDraft): void {
  try {
    sessionStorage.setItem("reel-still.sequence-draft", JSON.stringify(draft))
  } catch {
    // Private-browsing storage may be unavailable; the draft then lives in memory only.
  }
}

// Applied to the latest draft, and a no-op for the same audio, so a repeated sync cannot undo a clear.
export function withAudio(draft: SequenceDraft, audio: SequenceDraft["audio"]): SequenceDraft {
  const current = draft.audio
  if (current === audio) return draft
  if (current !== null && audio !== null && current.assetId === audio.assetId) return draft
  return { ...draft, audio }
}
