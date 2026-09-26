import { describe, expect, it } from "vitest"
import type { LibraryItem } from "../../api/library"
import { groupRailItemsByDay } from "./groupRailItemsByDay"

function item(id: string, createdAt: string): LibraryItem {
  return {
    id,
    kind: "video",
    status: "succeeded",
    preset_slug: null,
    preset_name: null,
    prompt: null,
    thumbnail_url: null,
    video_url: null,
    image_urls: [],
    images: [],
    generated_by: null,
    created_at: createdAt,
    error_message: null,
  }
}

const NOW = new Date("2026-09-25T12:00:00Z")

describe("groupRailItemsByDay", () => {
  it("labels today and yesterday", () => {
    const groups = groupRailItemsByDay(
      [item("a", "2026-09-25T09:00:00Z"), item("b", "2026-09-24T09:00:00Z")],
      NOW,
    )
    expect(groups.map((group) => group.heading)).toEqual(["Today", "Yesterday"])
  })

  it("uses the date for older items and keeps newest first", () => {
    const groups = groupRailItemsByDay(
      [item("a", "2026-09-25T09:00:00Z"), item("b", "2026-09-20T09:00:00Z")],
      NOW,
    )
    expect(groups[1].heading).toBe("20 Sep")
    expect(groups[0].items[0].id).toBe("a")
  })

  it("groups same-day items together", () => {
    const groups = groupRailItemsByDay(
      [item("a", "2026-09-25T09:00:00Z"), item("b", "2026-09-25T11:00:00Z")],
      NOW,
    )
    expect(groups).toHaveLength(1)
    expect(groups[0].items).toHaveLength(2)
  })
})
