import { useEffect, useState } from "react"

const reducedMotionQuery = "(prefers-reduced-motion: reduce)"

function readReducedMotion(): boolean {
  return window.matchMedia(reducedMotionQuery).matches
}

export function usePrefersReducedMotion(): boolean {
  const [hasReducedMotion, setHasReducedMotion] = useState(readReducedMotion)

  useEffect(() => {
    const mediaQuery = window.matchMedia(reducedMotionQuery)
    const updatePreference = () => setHasReducedMotion(mediaQuery.matches)
    updatePreference()
    mediaQuery.addEventListener("change", updatePreference)
    return () => mediaQuery.removeEventListener("change", updatePreference)
  }, [])

  return hasReducedMotion
}
