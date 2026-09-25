import { describe, expect, it } from "vitest"
import { formatSeconds, shareCopy } from "./shareCopy"

const { shareMeta, shareTitle, documentTitle } = shareCopy.page

describe("share meta", () => {
  it("reads clip · duration for videos", () => {
    expect(shareMeta({ kind: "video", clip_count: null, duration_ms: 5000, image_urls: [] })).toBe(
      "clip \u00b7 0:05",
    )
  })

  it("reads shots · duration for sequences", () => {
    expect(
      shareMeta({ kind: "sequence", clip_count: 3, duration_ms: 14_000, image_urls: [] }),
    ).toBe("3 shots \u00b7 0:14")
  })

  it("counts stills for images", () => {
    expect(
      shareMeta({ kind: "image", clip_count: null, duration_ms: null, image_urls: ["a", "b"] }),
    ).toBe("2 stills")
  })
})

describe("share title", () => {
  it("uses Sequence, Still and the preset name", () => {
    expect(shareTitle({ kind: "sequence", preset_name: null })).toBe("Sequence")
    expect(shareTitle({ kind: "image", preset_name: null })).toBe("Still")
    expect(shareTitle({ kind: "video", preset_name: "Dolly in" })).toBe("Dolly in")
  })

  it("seals the document title with the brand", () => {
    expect(documentTitle("Sequence")).toBe("Sequence \u00b7 Reel & Still")
  })

  it("formats durations as m:ss", () => {
    expect(formatSeconds(65_000)).toBe("1:05")
    expect(formatSeconds(null)).toBeNull()
  })
})
