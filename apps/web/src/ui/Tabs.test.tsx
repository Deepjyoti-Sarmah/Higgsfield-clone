import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { Tabs, type TabItem } from "./Tabs"
import { nextTabIndex } from "./tabKeys"

const items: readonly TabItem<string>[] = [
  { value: "still", label: "Still" },
  { value: "clip", label: "Clip" },
  { value: "sequence", label: "Sequence" },
]

describe("nextTabIndex", () => {
  it("moves right and wraps to the first tab", () => {
    expect(nextTabIndex(3, 0, "ArrowRight")).toBe(1)
    expect(nextTabIndex(3, 2, "ArrowRight")).toBe(0)
  })

  it("moves left and wraps to the last tab", () => {
    expect(nextTabIndex(3, 1, "ArrowLeft")).toBe(0)
    expect(nextTabIndex(3, 0, "ArrowLeft")).toBe(2)
  })

  it("jumps with Home and End", () => {
    expect(nextTabIndex(3, 1, "Home")).toBe(0)
    expect(nextTabIndex(3, 1, "End")).toBe(2)
  })

  it("keeps the index for unrelated keys", () => {
    expect(nextTabIndex(3, 1, "a")).toBe(1)
  })
})

describe("Tabs rendering", () => {
  it("marks only the active tab with aria-selected", () => {
    const markup = renderToStaticMarkup(
      <Tabs items={items} value="clip" onChange={() => {}} ariaLabel="Composer" />,
    )
    expect(markup).toContain('aria-label="Composer"')
    expect(markup).toContain('role="tablist"')
    expect((markup.match(/aria-selected="true"/g) ?? []).length).toBe(1)
    expect(markup).toContain('aria-selected="false"')
    expect(markup).toMatch(/>Still</)
    expect(markup).toMatch(/>Clip</)
    expect(markup).toMatch(/>Sequence</)
  })

  it("gives the active tab tabbable focus and others -1", () => {
    const markup = renderToStaticMarkup(
      <Tabs items={items} value="sequence" onChange={() => {}} ariaLabel="Composer" />,
    )
    expect(markup).toContain('tabindex="0"')
    expect((markup.match(/tabindex="-1"/g) ?? []).length).toBe(2)
  })
})
