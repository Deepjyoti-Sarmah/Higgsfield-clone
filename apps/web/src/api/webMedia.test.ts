import { describe, expect, it } from "vitest"
import { SHOWCASE } from "./webMedia"

describe("showcase config", () => {
  it("has all four items, each with a url and a caption", () => {
    const keys = ["still", "clip", "faceswap", "sequence"] as const
    for (const key of keys) {
      const item = SHOWCASE[key]
      expect(item.url.length).toBeGreaterThan(0)
      expect(item.caption.length).toBeGreaterThan(0)
    }
  })

  it("gives the video items a poster fallback", () => {
    expect(SHOWCASE.clip.poster).not.toBeNull()
    expect(SHOWCASE.sequence.poster).not.toBeNull()
  })
})
