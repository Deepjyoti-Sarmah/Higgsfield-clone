import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"
import { useGuestSessionRunner } from "./guestSession"
import type { GuestSessionSource, RunWithGuestSession } from "./guestSession"

export type LedgerEntry = components["schemas"]["LedgerEntryResponse"]

export type LedgerState = {
  status: "idle" | "loading" | "ready" | "error"
  items: LedgerEntry[]
  reload: () => void
}

const LEDGER_LIMIT = 10

async function fetchLedger(run: RunWithGuestSession): Promise<LedgerEntry[] | null> {
  try {
    const outcome = await run(() =>
      apiClient.GET("/api/v1/credits/ledger", { params: { query: { limit: LEDGER_LIMIT } } }),
    )
    if (outcome.outcome !== "done") return null
    const { data, response } = outcome.result
    if (response.status !== 200 || !data) return null
    return data.items
  } catch {
    return null
  }
}

// Fetches the last 10 entries whenever the popover opens (isOpen rising edge)
// and whenever the caller bumps the nonce (after a top-up).
export function useLedger(
  session: GuestSessionSource,
  isOpen: boolean,
  reloadNonce: number,
): LedgerState {
  const run = useGuestSessionRunner(session)
  const [status, setStatus] = useState<LedgerState["status"]>("idle")
  const [items, setItems] = useState<LedgerEntry[]>([])
  const hasItemsRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const reload = useCallback(() => {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    if (!hasItemsRef.current) setStatus("loading")
    void fetchLedger(run).then((loaded) => {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      hasItemsRef.current = loaded !== null
      setItems(loaded ?? [])
      setStatus(loaded === null ? "error" : "ready")
    })
  }, [run])

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (isOpen) reload()
  }, [isOpen, reloadNonce, reload])

  return { status, items, reload }
}
