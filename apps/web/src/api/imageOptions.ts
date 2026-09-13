import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"

export type ImageOptions = components["schemas"]["ImageOptionsResponse"]

export type ImageOptionsState = {
  status: "loading" | "ready" | "error"
  options: ImageOptions | null
  reload: () => void
}

async function fetchImageOptions(): Promise<ImageOptions | null> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/image-options")
    if (response.status !== 200 || !data) return null
    return data
  } catch {
    return null
  }
}

export function useImageOptions(): ImageOptionsState {
  const [options, setOptions] = useState<ImageOptions | null>(null)
  const [status, setStatus] = useState<ImageOptionsState["status"]>("loading")
  const hasOptionsRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const reload = useCallback(() => {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    if (!hasOptionsRef.current) setStatus("loading")
    void fetchImageOptions().then((loaded) => {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      if (loaded === null) {
        setStatus("error")
        return
      }
      hasOptionsRef.current = true
      setOptions(loaded)
      setStatus("ready")
    })
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    reload()
    return () => {
      isMountedRef.current = false
    }
  }, [reload])

  return { status, options, reload }
}
