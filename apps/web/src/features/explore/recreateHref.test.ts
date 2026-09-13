import { expect, test } from "vitest"
import { recreateHref } from "./recreateHref"

test("builds the create-video deep link", () => {
  expect(recreateHref("dolly-in")).toBe("/create/video?preset=dolly-in")
})

test("url-encodes the slug", () => {
  expect(recreateHref("smash and grab")).toBe("/create/video?preset=smash%20and%20grab")
  expect(recreateHref("a/b&c=d")).toBe("/create/video?preset=a%2Fb%26c%3Dd")
})

test("round-trips through URLSearchParams", () => {
  const href = recreateHref("smash and grab")
  const params = new URLSearchParams(href.split("?")[1])
  expect(params.get("preset")).toBe("smash and grab")
})

test("keeps the path unencoded", () => {
  const [path] = recreateHref("orbit push").split("?")
  expect(path).toBe("/create/video")
})
