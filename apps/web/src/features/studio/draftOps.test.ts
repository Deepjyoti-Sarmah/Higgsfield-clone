import { beforeEach, describe, expect, it, vi } from "vitest"

// jsdom is not installed: stub the minimal sessionStorage surface draftOps uses.
class MemoryStorage {
  private map = new Map<string, string>()
  getItem(key: string) {
    return this.map.has(key) ? this.map.get(key)! : null
  }
  setItem(key: string, value: string) {
    this.map.set(key, String(value))
  }
  removeItem(key: string) {
    this.map.delete(key)
  }
  clear() {
    this.map.clear()
  }
}
vi.stubGlobal("sessionStorage", new MemoryStorage())

import {
  addClipToDraft,
  EMPTY_DRAFT,
  MAX_SEQUENCE_CLIPS,
  moveClipWithinDraft,
  readStoredDraft,
  removeClipFromDraft,
  setClipTransition,
  withAudio,
  writeStoredDraft,
} from "./draftOps"

const CLIP = { jobId: "job-1", posterUrl: null, aspect: null }

function fill(n: number) {
  let draft = EMPTY_DRAFT
  for (let index = 0; index < n; index += 1) {
    draft = addClipToDraft(draft, { ...CLIP, jobId: `job-${index}` }) ?? draft
  }
  return draft
}

describe("sequence draft rules", () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it("adds clips up to six then refuses", () => {
    expect(MAX_SEQUENCE_CLIPS).toBe(6)
    const full = fill(6)
    expect(full.clips).toHaveLength(6)
    expect(addClipToDraft(full, CLIP)).toBeNull()
  })

  it("forces the first transition to cut and defaults the rest to crossfade", () => {
    const draft = fill(2)
    expect(draft.clips[0].transitionIn).toBe("cut")
    expect(draft.clips[1].transitionIn).toBe("crossfade")
    const changed = setClipTransition(draft, 0, "fade_black")
    expect(changed.clips[0].transitionIn).toBe("cut")
  })

  it("moves a clip and removes one", () => {
    const draft = fill(3)
    const moved = moveClipWithinDraft(draft, 2, 0)
    expect(moved.clips.map((clip) => clip.jobId)).toEqual(["job-2", "job-0", "job-1"])
    const removed = removeClipFromDraft(moved, 1)
    expect(removed.clips.map((clip) => clip.jobId)).toEqual(["job-2", "job-1"])
  })

  it("restores the draft from sessionStorage", () => {
    writeStoredDraft(fill(2))
    expect(readStoredDraft().clips).toHaveLength(2)
    expect(readStoredDraft().clips[0].transitionIn).toBe("cut")
  })

  it("returns an empty draft for corrupt storage", () => {
    sessionStorage.setItem("reel-still.sequence-draft", "not json")
    expect(readStoredDraft()).toEqual(EMPTY_DRAFT)
  })
})

describe("withAudio", () => {
  const music = { assetId: "a1", name: "music.wav" }

  it("keeps the same draft when the same audio is set again", () => {
    const draft = { clips: [], audio: music }
    expect(withAudio(draft, { ...music })).toBe(draft)
  })

  it("applies to the latest draft, so a sync after clearing leaves the clips empty", () => {
    const cleared = withAudio(EMPTY_DRAFT, music)
    expect(cleared.clips).toEqual([])
    expect(cleared.audio).toEqual(music)
  })
})
