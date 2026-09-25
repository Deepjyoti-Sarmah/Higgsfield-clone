import { useCallback, useEffect, useRef, useState } from "react"

export type ClipAspects = Record<string, number>

// Reads each poster's naturalWidth/naturalHeight once and caches the aspect.
export function useClipAspects(items: { id: string; thumbnail_url: string | null }[]): ClipAspects {
  const [aspects, setAspects] = useState<ClipAspects>({})
  const cacheRef = useRef<ClipAspects>({})

  const recordAspect = useCallback((jobId: string, aspect: number) => {
    if (cacheRef.current[jobId] !== undefined) return
    cacheRef.current[jobId] = aspect
    setAspects((current) => ({ ...current, [jobId]: aspect }))
  }, [])

  useEffect(() => {
    for (const item of items) {
      if (item.thumbnail_url === null) continue
      if (cacheRef.current[item.id] !== undefined) continue
      const image = new Image()
      image.onload = () => {
        if (image.naturalWidth > 0 && image.naturalHeight > 0) {
          recordAspect(item.id, image.naturalWidth / image.naturalHeight)
        }
      }
      image.src = item.thumbnail_url
    }
  }, [items, recordAspect])

  return aspects
}
