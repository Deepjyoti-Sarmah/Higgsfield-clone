import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "../../api/client"
import type { Preset, PresetsState } from "./createVideoTypes"

async function fetchPresets(): Promise<Preset[] | null> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/presets")
    if (response.status !== 200 || !data) return null
    return data.presets
  } catch {
    return null
  }
}

export function usePresets(): PresetsState {
  const [presets, setPresets] = useState<Preset[]>([])
  const [status, setStatus] = useState<PresetsState["status"]>("loading")
  const hasPresetsRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const reloadPresets = useCallback(() => {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    if (!hasPresetsRef.current) setStatus("loading")
    void fetchPresets().then((loaded) => {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      if (!loaded) {
        setStatus("error")
        return
      }
      hasPresetsRef.current = true
      setPresets(loaded)
      setStatus("ready")
    })
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    reloadPresets()
    return () => {
      isMountedRef.current = false
    }
  }, [reloadPresets])

  return { status, presets, reloadPresets }
}
