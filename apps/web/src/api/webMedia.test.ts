import { describe, expect, it } from "vitest"
import { SHOWCASE } from "./webMedia"

describe("showcase config", () => {
  it("has all six items, each with a url and a caption", () => {
    const keys = ["still", "clip", "faceswap", "sequence", "orbitClip", "canyonStill"] as const
    for (const key of keys) {
      const item = SHOWCASE[key]
      expect(item.url.length).toBeGreaterThan(0)
      expect(item.caption.length).toBeGreaterThan(0)
    }
  })

  it("gives every tile a distinct url", () => {
    const urls = [SHOWCASE.still, SHOWCASE.clip, SHOWCASE.faceswap, SHOWCASE.sequence, SHOWCASE.orbitClip, SHOWCASE.canyonStill].map(
      (item) => item.url,
    )
    expect(new Set(urls).size).toBe(urls.length)
  })

  it("gives the video items a poster fallback", () => {
    expect(SHOWCASE.clip.poster).not.toBeNull()
    expect(SHOWCASE.sequence.poster).not.toBeNull()
    expect(SHOWCASE.orbitClip.poster).not.toBeNull()
  })
})
