import { expect, test } from "vitest"
import { formatCreatedAt } from "./formatCreatedAt"

test("formats an evening UTC timestamp", () => {
  expect(formatCreatedAt("2026-09-13T19:40:00Z")).toBe("13 Sep 2026, 19:40")
})

test("renders midnight with a two-digit hour", () => {
  expect(formatCreatedAt("2026-09-13T00:05:00Z")).toBe("13 Sep 2026, 00:05")
})

test("returns an empty string for empty input", () => {
  expect(formatCreatedAt("")).toBe("")
})

test("returns an empty string for unparsable input", () => {
  expect(formatCreatedAt("not a date")).toBe("")
})
