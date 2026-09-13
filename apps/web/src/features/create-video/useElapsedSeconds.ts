import { useEffect, useState } from "react"

const TICK_MS = 1000

function computeElapsedSeconds(startIso: string | null, endIso: string | null): number {
  if (startIso === null) return 0
  const start = Date.parse(startIso)
  const end = endIso === null ? Date.now() : Date.parse(endIso)
  return Math.max(0, Math.floor((end - start) / 1000))
}

export function useElapsedSeconds(startIso: string | null, endIso: string | null): number {
  const [seconds, setSeconds] = useState(() => computeElapsedSeconds(startIso, endIso))

  useEffect(() => {
    setSeconds(computeElapsedSeconds(startIso, endIso))
    if (startIso === null || endIso !== null) return
    const timer = setInterval(
      () => setSeconds(computeElapsedSeconds(startIso, endIso)),
      TICK_MS,
    )
    return () => clearInterval(timer)
  }, [startIso, endIso])

  return seconds
}
