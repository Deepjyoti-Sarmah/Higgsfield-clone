import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"
import { useGuestSessionRunner } from "./guestSession"
import type { GuestSessionSource, RunWithGuestSession } from "./guestSession"

export type LibraryItem = components["schemas"]["LibraryItemResponse"]

export type LibraryState = {
  status: "loading" | "ready" | "error"
  items: LibraryItem[]
  reloadLibrary: () => void
}

async function fetchLibrary(runWithGuestSession: RunWithGuestSession): Promise<LibraryItem[] | null> {
  try {
    const outcome = await runWithGuestSession(() =>
      apiClient.GET("/api/v1/jobs", { params: { query: { limit: 50 } } }),
    )
    if (outcome.outcome !== "done") return null
    const { data, response } = outcome.result
    if (response.status !== 200 || !data) return null
    return data.items
  } catch {
    return null
  }
}

export function useLibrary(session: GuestSessionSource): LibraryState {
  const runWithGuestSession = useGuestSessionRunner(session)
  const [items, setItems] = useState<LibraryItem[]>([])
  const [status, setStatus] = useState<LibraryState["status"]>("loading")
  const hasItemsRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const reloadLibrary = useCallback(() => {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    if (!hasItemsRef.current) setStatus("loading")
    void fetchLibrary(runWithGuestSession).then((loaded) => {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      if (!loaded) {
        setStatus("error")
        return
      }
      hasItemsRef.current = true
      setItems(loaded)
      setStatus("ready")
    })
  }, [runWithGuestSession])

  useEffect(() => {
    isMountedRef.current = true
    reloadLibrary()
    return () => {
      isMountedRef.current = false
    }
  }, [reloadLibrary])

  return { status, items, reloadLibrary }
}
