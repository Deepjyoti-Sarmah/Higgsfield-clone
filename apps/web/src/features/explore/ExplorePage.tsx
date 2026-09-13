import { useEffect } from "react"
import { usePresets } from "../../api/presets"
import { ExploreHero } from "./ExploreHero"
import { PresetGallery } from "./PresetGallery"
import { ToolCards } from "./ToolCards"

function useExploreTitle(): void {
  useEffect(() => {
    document.title = "Explore · Higgsfield"
    return () => {
      document.title = "Higgsfield"
    }
  }, [])
}

export function ExplorePage() {
  const presets = usePresets()
  useExploreTitle()

  return (
    <div className="flex flex-col gap-8">
      <ExploreHero />
      <ToolCards />
      <PresetGallery state={presets} />
    </div>
  )
}
