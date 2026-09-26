import { describe, expect, it } from "vitest"
import { checkImageFile, submitBlockedReason, wellInput } from "./faceSwapTypes"
import type { WellState } from "./faceSwapTypes"

const IDLE: WellState = { status: "idle" }
const READY: WellState = {
  status: "ready",
  file: new File([], "a.png"),
  previewUrl: "blob:ready",
  asset: { id: "asset-1", kind: "input_image", status: "ready", content_type: "image/png", byte_size: 1, url: null },
}
describe("wellInput", () => {
  it("prefers a seed over an upload", () => {
    expect(wellInput("seed-1", "https://seed", READY)).toEqual({
      assetId: "seed-1",
      previewUrl: "https://seed",
      fromSeed: true,
    })
  })

  it("falls back to a ready upload", () => {
    expect(wellInput(null, null, READY)).toEqual({
      assetId: "asset-1",
      previewUrl: "blob:ready",
      fromSeed: false,
    })
  })

  it("is null when nothing is ready", () => {
    expect(wellInput(null, null, IDLE)).toBeNull()
  })
})

describe("submitBlockedReason", () => {
  const target = wellInput("target-1", "https://target", IDLE)

  it("blocks on a missing face first", () => {
    expect(submitBlockedReason(null, target, false)).toBe("no-face")
  })

  it("blocks on a missing target", () => {
    const face = wellInput("face-1", "https://face", IDLE)
    expect(submitBlockedReason(face, null, false)).toBe("no-target")
  })

  it("blocks while a well is still uploading", () => {
    const face = wellInput("face-1", "https://face", IDLE)
    expect(submitBlockedReason(face, target, true)).toBe("uploading")
  })

  it("is unblocked once both wells are ready", () => {
    const face = wellInput("face-1", "https://face", IDLE)
    expect(submitBlockedReason(face, target, false)).toBeNull()
  })
})

describe("checkImageFile", () => {
  it("accepts an in-range jpeg/png/webp", () => {
    expect(checkImageFile(new File(["x"], "a.png", { type: "image/png" }))).toBe(true)
  })

  it("rejects an unsupported type", () => {
    expect(checkImageFile(new File(["x"], "a.gif", { type: "image/gif" }))).toBe(false)
  })

  it("rejects an empty file", () => {
    expect(checkImageFile(new File([], "a.png", { type: "image/png" }))).toBe(false)
  })
})
