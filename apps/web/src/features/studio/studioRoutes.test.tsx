import { describe, expect, it } from "vitest"
import { studioCopy } from "./studioCopy"

// Mirrors the redirect maths in App.tsx: keep all params, rename job→item.
function redirectSearch(from: string, set?: [string, string]): string {
  const params = new URLSearchParams(from)
  if (set) {
    const [name, value] = set
    params.set(name, value)
  }
  return params.toString()
}

function libraryRedirectSearch(from: string): string {
  const params = new URLSearchParams(from)
  const job = params.get("job")
  params.delete("job")
  if (job !== null) params.set("item", job)
  return params.toString()
}

describe("studio redirects", () => {
  it("renames ?job= to ?item= and keeps other params", () => {
    expect(libraryRedirectSearch("?job=abc&x=1")).toBe("x=1&item=abc")
    expect(libraryRedirectSearch("")).toBe("")
  })

  it("sets the tab for create redirects, keeping other params", () => {
    expect(redirectSearch("?a=b", ["tab", "clip"])).toBe("a=b&tab=clip")
    expect(redirectSearch("", ["tab", "still"])).toBe("tab=still")
  })

  it("opens credits and keeps other params", () => {
    expect(redirectSearch("?item=j1", ["credits", "open"])).toBe("item=j1&credits=open")
  })
})

describe("studio tool guidance", () => {
  it("numbers all four tools in the flow order and explains each one", () => {
    expect(studioCopy.toolOrder).toEqual(["still", "clip", "sequence", "faceswap"])
    studioCopy.toolOrder.forEach((tab, index) => {
      const tool = studioCopy.tools[tab]
      expect(tool.step).toBe(index + 1)
      expect(tool.label.length).toBeGreaterThan(0)
      expect(tool.purpose.length).toBeGreaterThan(0)
      expect(tool.output.length).toBeGreaterThan(0)
      expect(tool.next.length).toBeGreaterThan(0)
    })
  })

  it("gives the rail a heading, a count, and a New action", () => {
    expect(studioCopy.rail.heading).toBe("Your work")
    expect(studioCopy.rail.count(1)).toBe("1 generation")
    expect(studioCopy.rail.count(4)).toBe("4 generations")
    expect(studioCopy.rail.newAction).toContain("New")
  })

  it("tells the empty stage what it shows and how to start", () => {
    expect(studioCopy.stage.empty.title.length).toBeGreaterThan(0)
    expect(studioCopy.stage.empty.body).toContain("composer")
    expect(studioCopy.stage.empty.action).toContain("Still")
  })

  it("keeps the flow strip heading available for every tab", () => {
    expect(studioCopy.flowStrip.heading).toBe("How this works")
  })
})
