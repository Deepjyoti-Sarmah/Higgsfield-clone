import { useCallback, useState } from "react"
import { TOP_UP_CREDITS, useCreditBalance } from "../../api/credits"
import { useLedger } from "../../api/ledger"
import type { GuestSessionSource } from "../../api/guestSession"
import { useGuestSessionRunner } from "../../api/guestSession"
import { sendTopUp } from "../../api/credits"
import { Button } from "../../ui/Button"
import { LedgerList } from "./LedgerList"

type CreditsPopoverPanelProps = {
  session: GuestSessionSource
}

async function requestTopUp(run: ReturnType<typeof useGuestSessionRunner>): Promise<boolean> {
  return sendTopUp(run)
}

function BalanceBlock({ session }: { session: GuestSessionSource }) {
  const balance = useCreditBalance(session)
  if (balance.status === "known" && balance.balance !== null) {
    return <p className="font-mono text-6xl leading-none text-text">{balance.balance}</p>
  }
  if (balance.status === "error") {
    return (
      <Button variant="secondary" onClick={balance.refresh}>
        Retry
      </Button>
    )
  }
  return <p className="font-mono text-6xl leading-none text-faint">·</p>
}

function TopUpBlock({ session, onGranted }: {
  session: GuestSessionSource
  onGranted: () => void
}) {
  const run = useGuestSessionRunner(session)
  const [isToppingUp, setIsToppingUp] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const handleTopUp = useCallback(() => {
    if (isToppingUp) return
    setIsToppingUp(true)
    setError(null)
    void requestTopUp(run)
      .then((ok) => (ok ? onGranted() : setError("The top-up didn't go through. Try again.")))
      .finally(() => setIsToppingUp(false))
  }, [isToppingUp, onGranted, run])
  return (
    <div className="flex flex-col items-start gap-1">
      <Button onClick={handleTopUp} isLoading={isToppingUp}>
        Add demo credits ({TOP_UP_CREDITS})
      </Button>
      <p className="text-[13px] text-faint">Demo credits. No payment is taken.</p>
      {error && (
        <p role="alert" className="text-[13px] text-danger">
          {error}
        </p>
      )}
    </div>
  )
}

export function CreditsPopoverPanel({ session }: CreditsPopoverPanelProps) {
  const [topUpNonce, setTopUpNonce] = useState(0)
  const ledger = useLedger(session, true, topUpNonce)
  return (
    <div className="flex w-full flex-col gap-4">
      <div>
        <p className="text-sm text-muted">Credits</p>
        <BalanceBlock session={session} />
      </div>
      <TopUpBlock session={session} onGranted={() => setTopUpNonce((nonce) => nonce + 1)} />
      <LedgerList state={ledger} />
    </div>
  )
}
