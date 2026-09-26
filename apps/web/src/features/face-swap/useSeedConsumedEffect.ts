import { useEffect, useRef } from "react"
import type { SeedImage } from "../../api/studioContracts"

// Tells the parent its seed was adopted, once per distinct seed asset id.
export function useSeedConsumedEffect(seed: SeedImage | null, onConsumed: () => void): void {
  const adoptedRef = useRef<string | null>(null)
  const consumeRef = useRef(onConsumed)
  consumeRef.current = onConsumed

  useEffect(() => {
    if (seed === null || adoptedRef.current === seed.assetId) return
    adoptedRef.current = seed.assetId
    consumeRef.current()
  }, [seed])
}
