import { useCallback, useEffect, useRef, useState } from "react"
import { listenForCreditsChanged } from "./creditsSignal"
import { apiClient } from "./client"
import type { components } from "./generated/schema"
import { useGuestSessionRunner } from "./guestSession"
import type { GuestSessionSource, RunWithGuestSession } from "./guestSession"

export type TopUpResult = components["schemas"]["TopUpResponse"]

export const TOP_UP_CREDITS = 100

export type TopUpStatus = "idle" | "pending" | "done" | "error"
export type BalanceStatus = "loading" | "known" | "error"

async function fetchBalance(runWithGuestSession: RunWithGuestSession): Promise<number | null> {
  try {
    const outcome = await runWithGuestSession(() => apiClient.GET("/api/v1/credits"))
    if (outcome.outcome !== "done") return null
    const { data, response } = outcome.result
    if (response.status !== 200 || !data) return null
    return data.balance
  } catch {
    return null
  }
}

async function sendTopUp(runWithGuestSession: RunWithGuestSession): Promise<boolean> {
  try {
    const outcome = await runWithGuestSession(() => apiClient.POST("/api/v1/credits/topup"))
    if (outcome.outcome !== "done") return false
    return outcome.result.response.status === 200 && outcome.result.data !== undefined
  } catch {
    return false
  }
}

export { sendTopUp }

type BalanceState = {
  status: BalanceStatus
  balance: number | null
  reload: () => void
  applyBalance: (next: number) => void
}

function useBalanceState(runWithGuestSession: RunWithGuestSession): BalanceState {
  const [status, setStatus] = useState<BalanceStatus>("loading")
  const [balance, setBalance] = useState<number | null>(null)
  const hasBalanceRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const reload = useCallback(() => {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    if (!hasBalanceRef.current) setStatus("loading")
    void fetchBalance(runWithGuestSession).then((loaded) => {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      if (loaded === null) {
        setStatus("error")
        return
      }
      hasBalanceRef.current = true
      setBalance(loaded)
      setStatus("known")
    })
  }, [runWithGuestSession])

  const applyBalance = useCallback((next: number) => {
    hasBalanceRef.current = true
    setBalance(next)
    setStatus("known")
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    reload()
    return () => {
      isMountedRef.current = false
    }
  }, [reload])

  return { status, balance, reload, applyBalance }
}

export type CreditBalanceState = {
  status: BalanceStatus
  balance: number | null
  refresh: () => void
  applyKnownBalance: (balance: number) => void
}

export function useCreditBalance(session: GuestSessionSource): CreditBalanceState {
  const runWithGuestSession = useGuestSessionRunner(session)
  const balanceState = useBalanceState(runWithGuestSession)
  const { reload } = balanceState
  useEffect(() => listenForCreditsChanged(reload), [reload])

  return {
    status: balanceState.status,
    balance: balanceState.balance,
    refresh: balanceState.reload,
    applyKnownBalance: balanceState.applyBalance,
  }
}
