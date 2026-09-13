import { expect, test } from "vitest"
import { formatElapsed } from "./elapsedTime"

test("formats zero and single-digit seconds", () => {
  expect(formatElapsed(0)).toBe("0:00")
  expect(formatElapsed(7)).toBe("0:07")
})

test("formats minutes with a two-digit seconds part", () => {
  expect(formatElapsed(102)).toBe("1:42")
  expect(formatElapsed(725)).toBe("12:05")
})

test("clamps negative input to zero", () => {
  expect(formatElapsed(-5)).toBe("0:00")
})
