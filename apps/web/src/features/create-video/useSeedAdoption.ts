import { useEffect, useRef } from "react"
import type { SeedImage } from "../../api/studioContracts"

// Calls onConsumed once per distinct seed asset id.
export function useSeedAdoption(
  seed: SeedImage | null,
  onConsumed: () => void,
): void {
  const adoptedRef = useRef<string | null>(null)
  const consumeRef = useRef(onConsumed)
  consumeRef.current = onConsumed

  useEffect(() => {
    if (seed === null || adoptedRef.current === seed.assetId) return
    adoptedRef.current = seed.assetId
    consumeRef.current()
  }, [seed])
}
