import { describe, expect, it } from "vitest"
import type { LibraryItem } from "../../api/library"
import { countRailKinds, matchesRailKindFilter } from "./railKindFilter"

function item(id: string, kind: LibraryItem["kind"]): LibraryItem {
  return {
    id,
    kind,
    status: "succeeded",
    preset_slug: null,
    preset_name: null,
    prompt: null,
    thumbnail_url: null,
    video_url: null,
    image_urls: [],
    images: [],
    clip_count: null,
    duration_ms: null,
    generated_by: null,
    created_at: "2026-09-25T09:00:00Z",
    error_message: null,
  }
}

describe("railKindFilter", () => {
  it("matches all and single kinds", () => {
    const still = item("a", "image")
    expect(matchesRailKindFilter(still, "all")).toBe(true)
    expect(matchesRailKindFilter(still, "image")).toBe(true)
    expect(matchesRailKindFilter(still, "video")).toBe(false)
  })

  it("groups still and video face swaps under the faceswap filter", () => {
    expect(matchesRailKindFilter(item("a", "faceswap"), "faceswap")).toBe(true)
    expect(matchesRailKindFilter(item("b", "video_faceswap"), "faceswap")).toBe(true)
    expect(matchesRailKindFilter(item("c", "video"), "faceswap")).toBe(false)
  })

  it("counts each kind plus the total", () => {
    const items = [item("a", "image"), item("b", "video"), item("c", "video")]
    expect(countRailKinds(items)).toEqual({
      all: 3,
      image: 1,
      video: 2,
      sequence: 0,
      faceswap: 0,
    })
  })

  it("counts both face swap kinds toward the faceswap count", () => {
    const items = [item("a", "image"), item("b", "faceswap"), item("c", "video_faceswap")]
    expect(countRailKinds(items)).toEqual({
      all: 3,
      image: 1,
      video: 0,
      sequence: 0,
      faceswap: 2,
    })
  })
})
