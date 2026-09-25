import { describe, expect, it, vi } from "vitest"
import { renderToStaticMarkup } from "react-dom/server"
import { MemoryRouter } from "react-router-dom"

const presetsState = {
  status: "ready" as const,
  presets: [
    {
      slug: "dolly-in",
      name: "Dolly in",
      description: "",
      category: "camera" as const,
      credit_cost: 20,
      preview_url: null,
    },
  ],
  reloadPresets: () => undefined,
}

vi.mock("../../api/presets", () => ({
  usePresets: () => presetsState,
}))

const { StartPage } = await import("./StartPage")
const { PresetChipRow } = await import("./PresetChipRow")

function render(node: React.ReactElement): string {
  return renderToStaticMarkup(<MemoryRouter>{node}</MemoryRouter>)
}

describe("start page", () => {
  it("renders exactly one primary CTA pointing at /studio", () => {
    const html = render(<StartPage />)
    const ctaMatches = html.match(/href="\/studio"/g) ?? []
    expect(ctaMatches.length).toBe(1)
    expect(html).toContain("Open the studio")
  })

  it("links preset chips into the clip tab with the preset slug", () => {
    const html = render(<PresetChipRow presetsState={presetsState} />)
    expect(html).toContain('href="/studio?tab=clip&amp;preset=dolly-in"')
  })

  it("shows skeletons while presets load and nothing on error", () => {
    const loading = render(
      <PresetChipRow presetsState={{ ...presetsState, status: "loading", presets: [] }} />,
    )
    expect(loading).toContain("aria-busy")
    const failed = render(
      <PresetChipRow presetsState={{ ...presetsState, status: "error", presets: [] }} />,
    )
    expect(failed).not.toContain("preset=")
  })
})
