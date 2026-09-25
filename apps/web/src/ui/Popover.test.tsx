import { renderToStaticMarkup } from "react-dom/server"
import { describe, expect, it } from "vitest"
import { Popover } from "./Popover"
import { isDismissKey } from "./popoverKeys"

describe("isDismissKey", () => {
  it("closes on Escape only", () => {
    expect(isDismissKey("Escape")).toBe(true)
    expect(isDismissKey("Enter")).toBe(false)
    expect(isDismissKey("Tab")).toBe(false)
  })
})

describe("Popover rendering", () => {
  it("does not render the panel while closed", () => {
    const markup = renderToStaticMarkup(
      <Popover trigger={(props) => <button type="button" {...props}>Credits</button>}>
        Balance
      </Popover>,
    )
    expect(markup).toMatch(/>Credits</)
    expect(markup).not.toContain("Balance")
  })
})
