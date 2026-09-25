import { describe, expect, it } from "vitest"

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
