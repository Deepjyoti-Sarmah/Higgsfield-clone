import { describe, expect, it } from "vitest"
import { progressPathFor } from "./jobProgress"

describe("progressPathFor", () => {
  it("picks the right endpoint per kind", () => {
    expect(progressPathFor("video")).toBe("/api/v1/jobs/{job_id}")
    expect(progressPathFor("image")).toBe("/api/v1/image-jobs/{job_id}")
    expect(progressPathFor("sequence")).toBe("/api/v1/sequence-jobs/{job_id}")
    expect(progressPathFor("faceswap")).toBe("/api/v1/faceswap-jobs/{job_id}")
  })
})
