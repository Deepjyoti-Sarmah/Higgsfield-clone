import { describe, expect, it } from "vitest"
import { stillBlockedReason, stillJobBody } from "./stillSubmit"

describe("still job body", () => {
  it("carries the settings and an idempotency key", () => {
    const body = stillJobBody(
      { prompt: "a cat", aspect_ratio: "16:9", quality: "high", count: 2 },
      "key-1",
    )
    expect(body).toEqual({
      prompt: "a cat",
      aspect_ratio: "16:9",
      quality: "high",
      count: 2,
      idempotency_key: "key-1",
    })
  })
})

describe("still blocked reasons", () => {
  it("disables Generate on an empty or whitespace prompt", () => {
    expect(stillBlockedReason("", true)).toBe("no-prompt")
    expect(stillBlockedReason("   ", true)).toBe("no-prompt")
    expect(stillBlockedReason("a cat on a roof", true)).toBeNull()
  })

  it("reports unavailable options before the prompt", () => {
    expect(stillBlockedReason("a cat", false)).toBe("options-unavailable")
  })
})
