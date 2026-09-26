import { useState } from "react"
import type { SeedImage } from "../../api/studioContracts"

// The parent clears its seed once adopted, so keep our own copy until dropped.
export function useHeldSeed(seed: SeedImage | null): { active: SeedImage | null; drop: () => void } {
  const [held, setHeld] = useState<SeedImage | null>(seed)
  const [dropped, setDropped] = useState(false)
  if (seed !== null && seed.assetId !== held?.assetId) {
    setHeld(seed)
    setDropped(false)
  }
  return { active: dropped ? null : held, drop: () => setDropped(true) }
}
