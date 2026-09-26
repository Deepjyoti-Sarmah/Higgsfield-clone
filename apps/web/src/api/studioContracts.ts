import type { LibraryItem } from "./library"

export type StudioTab = "still" | "clip" | "sequence" | "faceswap"
export type SeedImage = { assetId: string; url: string }
export type FaceSwapSeed = SeedImage
export type SequenceTransition = "cut" | "crossfade" | "fade_black"
export type SequenceDraftClip = {
  jobId: string
  posterUrl: string | null
  aspect: number | null
  transitionIn: SequenceTransition
}
export type SequenceDraft = {
  clips: SequenceDraftClip[]
  audio: { assetId: string; name: string } | null
}
export type SequenceDraftControls = {
  draft: SequenceDraft
  addClip: (clip: Omit<SequenceDraftClip, "transitionIn">) => boolean
  removeClip: (index: number) => void
  moveClip: (from: number, to: number) => void
  setTransition: (index: number, transition: SequenceTransition) => void
  setAudio: (audio: SequenceDraft["audio"]) => void
  clearDraft: () => void
}
export type ComposerProps = { onJobStarted: (jobId: string) => void }
export type ClipComposerProps = ComposerProps & {
  seedImage: SeedImage | null
  onSeedConsumed: () => void
}
export type SequenceComposerProps = ComposerProps & {
  sequence: SequenceDraftControls
  libraryItems: LibraryItem[]
}
export type FaceSwapComposerProps = ComposerProps & {
  seedTarget: FaceSwapSeed | null
  onSeedConsumed: () => void
}
