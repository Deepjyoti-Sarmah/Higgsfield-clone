import { useEffect, useState } from "react"
import type { SequenceDraft, SequenceDraftControls } from "../../api/studioContracts"
import {
  addClipToDraft,
  moveClipWithinDraft,
  readStoredDraft,
  removeClipFromDraft,
  setClipTransition,
  writeStoredDraft,
} from "./draftOps"

export function useSequenceDraft(): SequenceDraftControls {
  const [draft, setDraft] = useState<SequenceDraft>(readStoredDraft)

  useEffect(() => {
    writeStoredDraft(draft)
  }, [draft])

  return {
    draft,
    addClip: (clip) => {
      const next = addClipToDraft(draft, clip)
      if (next === null) return false
      setDraft(next)
      return true
    },
    removeClip: (index) => setDraft(removeClipFromDraft(draft, index)),
    moveClip: (from, to) => setDraft(moveClipWithinDraft(draft, from, to)),
    setTransition: (index, transition) => setDraft(setClipTransition(draft, index, transition)),
    setAudio: (audio) => setDraft({ ...draft, audio }),
    clearDraft: () => setDraft({ clips: [], audio: null }),
  }
}
