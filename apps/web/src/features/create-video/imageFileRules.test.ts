import { expect, test } from "vitest"
import { ACCEPTED_IMAGE_TYPES, MAX_IMAGE_BYTES, checkImageFile } from "./imageFileRules"

function imageFile(type: string, size: number): File {
  return { type, size } as File
}

test("accepts jpeg, png and webp", () => {
  expect(ACCEPTED_IMAGE_TYPES).toEqual(["image/jpeg", "image/png", "image/webp"])
  for (const type of ACCEPTED_IMAGE_TYPES) {
    expect(checkImageFile(imageFile(type, 1024)), type).toBe(true)
  }
})

test("rejects gif and heic", () => {
  expect(checkImageFile(imageFile("image/gif", 1024))).toBe(false)
  expect(checkImageFile(imageFile("image/heic", 1024))).toBe(false)
})

test("rejects zero bytes and one byte over the limit", () => {
  expect(checkImageFile(imageFile("image/png", 0))).toBe(false)
  expect(checkImageFile(imageFile("image/png", MAX_IMAGE_BYTES + 1))).toBe(false)
})

test("accepts exactly the maximum byte size", () => {
  expect(MAX_IMAGE_BYTES).toBe(10_485_760)
  expect(checkImageFile(imageFile("image/png", MAX_IMAGE_BYTES))).toBe(true)
})
