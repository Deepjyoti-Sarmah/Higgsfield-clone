import { describe, expect, it } from "vitest"
import {
  MOTION_PREVIEWS,
  SHOWCASE_GALLERY,
  SHOWCASE_GROUPS,
  SHOWCASE_SEQUENCE,
  SHOWCASE_STILLS,
  findShowcaseItem,
} from "./webMedia"

const PRESET_SLUGS = [
  "dolly-in",
  "dolly-out",
  "pan-left",
  "pan-right",
  "tilt-up",
  "ken-burns",
  "orbit-push",
  "slow-drift",
  "crash-zoom",
  "whip-pan",
  "handheld",
  "spiral-in",
]

describe("motion previews", () => {
  it("exposes one preview per motion preset, each with a caption and a poster", () => {
    const slugs = MOTION_PREVIEWS.map((item) => item.id).sort()
    expect(slugs).toEqual([...PRESET_SLUGS].sort())
    for (const item of MOTION_PREVIEWS) {
      expect(item.url.endsWith(".mp4")).toBe(true)
      expect(item.poster).not.toBeNull()
      expect(item.caption).toContain(item.title)
    }
  })
})

describe("showcase gallery", () => {
  it("keeps the four local stills and the real sequence example", () => {
    expect(SHOWCASE_STILLS).toHaveLength(4)
    for (const item of SHOWCASE_STILLS) {
      expect(item.url.startsWith("/showcase/")).toBe(true)
      expect(item.caption.length).toBeGreaterThan(0)
    }
    expect(SHOWCASE_SEQUENCE.url.endsWith(".mp4")).toBe(true)
    expect(SHOWCASE_SEQUENCE.poster).not.toBeNull()
  })

  it("gives every gallery tile a distinct url and at least six tiles", () => {
    const urls = SHOWCASE_GALLERY.map((item) => item.url)
    expect(new Set(urls).size).toBe(urls.length)
    expect(urls.length).toBeGreaterThanOrEqual(6)
  })

  it("never puts two neighbouring tiles on the same source still", () => {
    for (let index = 0; index < SHOWCASE_GALLERY.length - 1; index += 1) {
      const current = SHOWCASE_GALLERY[index]
      const next = SHOWCASE_GALLERY[index + 1]
      expect(next.source).not.toBe(current.source)
    }
  })

  it("gives every gallery tile a source still", () => {
    for (const item of SHOWCASE_GALLERY) expect(item.source).not.toBeNull()
  })

  it("finds an item by id and rejects an unknown one", () => {
    expect(findShowcaseItem("dolly-in").url.endsWith("/previews/dolly-in.mp4")).toBe(true)
    expect(() => findShowcaseItem("nope")).toThrow("Unknown showcase item")
  })
})

describe("showcase groups", () => {
  it("puts one still on top of its three motion previews per source", () => {
    expect(SHOWCASE_GROUPS).toHaveLength(4)
    for (const group of SHOWCASE_GROUPS) {
      expect(group.still.kind).toBe("still")
      expect(group.previews).toHaveLength(3)
      for (const preview of group.previews) {
        expect(preview.kind).toBe("clip")
        expect(preview.source).toBe(group.source)
      }
    }
  })
})
