import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"
import { useGuestSessionRunner } from "./guestSession"
import type { GuestSessionSource, RunWithGuestSession } from "./guestSession"

export type TopUpResult = components["schemas"]["TopUpResponse"]

export const TOP_UP_CREDITS = 100

export type TopUpStatus = "idle" | "pending" | "done" | "error"
export type BalanceStatus = "loading" | "known" | "error"

export type CreditsPageState = {
  balanceStatus: BalanceStatus
  balance: number | null
  topUpStatus: TopUpStatus
  grantedAmount: number | null
  reload: () => void
  topUp: () => void
}

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

async function sendTopUp(runWithGuestSession: RunWithGuestSession): Promise<TopUpResult | null> {
  try {
    const outcome = await runWithGuestSession(() => apiClient.POST("/api/v1/credits/topup"))
    if (outcome.outcome !== "done") return null
    const { data, response } = outcome.result
    if (response.status !== 200 || !data) return null
    return data
  } catch {
    return null
  }
}

type BalanceState = {
  status: BalanceStatus
  balance: number | null
  reload: () => void
  applyTopUp: (result: TopUpResult) => void
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

  const applyTopUp = useCallback((result: TopUpResult) => {
    hasBalanceRef.current = true
    setBalance(result.balance)
    setStatus("known")
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    reload()
    return () => {
      isMountedRef.current = false
    }
  }, [reload])

  return { status, balance, reload, applyTopUp }
}

type TopUpState = {
  status: TopUpStatus
  grantedAmount: number | null
  topUp: () => void
}

function useTopUpState(
  runWithGuestSession: RunWithGuestSession,
  onGranted: (result: TopUpResult) => void,
): TopUpState {
  const [status, setStatus] = useState<TopUpStatus>("idle")
  const [grantedAmount, setGrantedAmount] = useState<number | null>(null)
  const isPendingRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const topUp = useCallback(() => {
    if (isPendingRef.current) return
    isPendingRef.current = true
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    setStatus("pending")
    void sendTopUp(runWithGuestSession).then((result) => {
      isPendingRef.current = false
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      if (result === null) {
        setStatus("error")
        return
      }
      setGrantedAmount(result.amount)
      onGranted(result)
      setStatus("done")
    })
  }, [runWithGuestSession, onGranted])

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  return { status, grantedAmount, topUp }
}

export function useCreditsPage(session: GuestSessionSource): CreditsPageState {
  const runWithGuestSession = useGuestSessionRunner(session)
  const balanceState = useBalanceState(runWithGuestSession)
  const topUpState = useTopUpState(runWithGuestSession, balanceState.applyTopUp)

  return {
    balanceStatus: balanceState.status,
    balance: balanceState.balance,
    topUpStatus: topUpState.status,
    grantedAmount: topUpState.grantedAmount,
    reload: balanceState.reload,
    topUp: topUpState.topUp,
  }
}
