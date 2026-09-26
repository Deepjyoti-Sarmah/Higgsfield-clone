import { useCallback, useEffect, useMemo, useState } from "react"
import type { SequenceDraft, SequenceDraftControls } from "../../api/studioContracts"
import {
  EMPTY_DRAFT,
  addClipToDraft,
  moveClipWithinDraft,
  readStoredDraft,
  removeClipFromDraft,
  setClipTransition,
  setClipTrim,
  withAudio,
  writeStoredDraft,
} from "./draftOps"

// Every updater is stable and functional: MusicDropZone re-runs its effect when setAudio changes,
// and a setAudio that closed over a stale draft used to restore cleared clips after Render.
export function useSequenceDraft(): SequenceDraftControls {
  const [draft, setDraft] = useState<SequenceDraft>(readStoredDraft)

  useEffect(() => {
    writeStoredDraft(draft)
  }, [draft])

  const addClip = useCallback<SequenceDraftControls["addClip"]>((clip) => {
    const next = addClipToDraft(draft, clip)
    if (next === null) return false
    setDraft(next)
    return true
  }, [draft])
  const removeClip = useCallback((index: number) => setDraft((prev) => removeClipFromDraft(prev, index)), [])
  const moveClip = useCallback(
    (from: number, to: number) => setDraft((prev) => moveClipWithinDraft(prev, from, to)),
    [],
  )
  const setTransition = useCallback<SequenceDraftControls["setTransition"]>(
    (index, transition) => setDraft((prev) => setClipTransition(prev, index, transition)),
    [],
  )
  const setTrim = useCallback<SequenceDraftControls["setTrim"]>(
    (index, trimStartMs, trimEndMs) => setDraft((prev) => setClipTrim(prev, index, trimStartMs, trimEndMs)),
    [],
  )
  const setAudio = useCallback<SequenceDraftControls["setAudio"]>(
    (audio) => setDraft((prev) => withAudio(prev, audio)),
    [],
  )
  const clearDraft = useCallback(() => setDraft(EMPTY_DRAFT), [])

  return useMemo(
    () => ({ draft, addClip, removeClip, moveClip, setTransition, setTrim, setAudio, clearDraft }),
    [draft, addClip, removeClip, moveClip, setTransition, setTrim, setAudio, clearDraft],
  )
}
