import { expect, test } from "vitest"
import type { Preset } from "../../api/presets"
import { groupPresetsByCategory } from "./groupPresetsByCategory"

function preset(slug: string, category: string): Preset {
  return {
    slug,
    name: slug,
    description: "",
    category: category as Preset["category"],
    credit_cost: 20,
    preview_url: null,
  }
}

test("orders groups camera, cinematic, dynamic", () => {
  const groups = groupPresetsByCategory([
    preset("d", "dynamic"),
    preset("c", "cinematic"),
    preset("a", "camera"),
  ])
  expect(groups.map((group) => group.category)).toEqual(["camera", "cinematic", "dynamic"])
})

test("omits empty categories", () => {
  const groups = groupPresetsByCategory([preset("a", "camera"), preset("b", "camera")])
  expect(groups).toHaveLength(1)
  expect(groups[0].category).toBe("camera")
})

test("keeps every input preset exactly once", () => {
  const groups = groupPresetsByCategory([
    preset("a", "dynamic"),
    preset("b", "camera"),
    preset("c", "camera"),
    preset("d", "cinematic"),
  ])
  const slugs = groups.flatMap((group) => group.presets.map((item) => item.slug))
  expect(slugs.sort()).toEqual(["a", "b", "c", "d"])
})

test("groups presets by their own category", () => {
  const groups = groupPresetsByCategory([preset("a", "dynamic"), preset("b", "camera")])
  expect(groups[0].presets.map((item) => item.slug)).toEqual(["b"])
  expect(groups[1].presets.map((item) => item.slug)).toEqual(["a"])
})

test("appends unknown categories in first-seen order instead of dropping them", () => {
  const groups = groupPresetsByCategory([
    preset("u1", "experimental"),
    preset("c1", "camera"),
    preset("u2", "portrait"),
    preset("u3", "experimental"),
  ])
  expect(groups.map((group) => group.category)).toEqual(["camera", "experimental", "portrait"])
  expect(groups[1].presets.map((item) => item.slug)).toEqual(["u1", "u3"])
})

test("returns nothing for no presets", () => {
  expect(groupPresetsByCategory([])).toEqual([])
})
