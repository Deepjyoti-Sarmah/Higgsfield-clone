import { describe, expect, it } from "vitest"
import { audioErrorKind, MAX_AUDIO_BYTES } from "./audioRules"

function fileOf(type: string, size: number): File {
  return { type, size } as File
}

describe("audio file rules", () => {
  it("accepts the three audio types within 10 MB", () => {
    expect(audioErrorKind(fileOf("audio/mpeg", 1000))).toBeNull()
    expect(audioErrorKind(fileOf("audio/mp4", 1000))).toBeNull()
    expect(audioErrorKind(fileOf("audio/wav", MAX_AUDIO_BYTES))).toBeNull()
  })

  it("rejects wrong types before any upload", () => {
    expect(audioErrorKind(fileOf("image/png", 1000))).toBe("wrong-type")
    expect(audioErrorKind(fileOf("video/mp4", 1000))).toBe("wrong-type")
  })

  it("rejects empty and oversized files", () => {
    expect(audioErrorKind(fileOf("audio/mpeg", 0))).toBe("empty")
    expect(audioErrorKind(fileOf("audio/mpeg", MAX_AUDIO_BYTES + 1))).toBe("too-large")
  })
})
