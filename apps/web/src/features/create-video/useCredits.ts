import { useCallback, useEffect, useReducer, useRef } from "react"
import { apiClient } from "../../api/client"
import type { BalanceView } from "./createVideoTypes"

export type CreditsControls = {
  balanceView: BalanceView
  balance: number | null
  refreshCredits: () => Promise<void>
  applyKnownBalance: (balance: number) => void
}

type CreditsState = { status: BalanceView["status"]; balance: number | null; isFirstLoad: boolean }
type CreditsAction =
  | { kind: "succeeded"; balance: number }
  | { kind: "failed"; status: "guest-offer" | "error" }
  | { kind: "session-ended" }

const initialCredits: CreditsState = { status: "guest-offer", balance: null, isFirstLoad: true }

function creditsReducer(_state: CreditsState, action: CreditsAction): CreditsState {
  if (action.kind === "session-ended") return initialCredits
  if (action.kind === "succeeded") {
    return { status: "known", balance: action.balance, isFirstLoad: false }
  }
  return { status: action.status, balance: null, isFirstLoad: false }
}

// A refresh keeps the last known balance visible instead of flashing "loading".
function deriveBalanceView(state: CreditsState): BalanceView {
  if (state.status === "known" && state.balance !== null) {
    return { status: "known", balance: state.balance }
  }
  if (state.status === "guest-offer") return { status: "guest-offer" }
  return state.isFirstLoad ? { status: "loading" } : { status: "error" }
}

async function fetchCredits(): Promise<CreditsAction> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/credits")
    if (response.status === 200 && data) return { kind: "succeeded", balance: data.balance }
    return { kind: "failed", status: response.status === 401 ? "guest-offer" : "error" }
  } catch {
    return { kind: "failed", status: "error" }
  }
}

export function useCredits(isSignedIn: boolean): CreditsControls {
  const [state, dispatch] = useReducer(creditsReducer, initialCredits)
  const isSignedInRef = useRef(isSignedIn)
  const requestIdRef = useRef(0)

  isSignedInRef.current = isSignedIn

  const refreshCredits = useCallback(async () => {
    if (!isSignedInRef.current) return
    const requestId = (requestIdRef.current += 1)
    const action = await fetchCredits()
    if (requestId !== requestIdRef.current) return
    dispatch(action)
  }, [])

  const applyKnownBalance = useCallback((known: number) => {
    requestIdRef.current += 1
    dispatch({ kind: "succeeded", balance: known })
  }, [])

  useEffect(() => {
    if (isSignedIn) {
      void refreshCredits()
      return
    }
    requestIdRef.current += 1
    dispatch({ kind: "session-ended" })
  }, [isSignedIn, refreshCredits])

  return {
    balanceView: deriveBalanceView(state),
    balance: state.balance,
    refreshCredits,
    applyKnownBalance,
  }
}
