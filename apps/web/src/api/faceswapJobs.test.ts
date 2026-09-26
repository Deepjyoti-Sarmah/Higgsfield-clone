import { describe, expect, it } from "vitest"
import { faceSwapJobBody } from "./faceswapJobs"

describe("face swap job body", () => {
  it("carries both asset ids and an idempotency key", () => {
    const body = faceSwapJobBody("face-1", "target-1", "key-1")
    expect(body).toEqual({
      source_asset_id: "face-1",
      target_asset_id: "target-1",
      idempotency_key: "key-1",
    })
  })
})
