import { TOP_UP_CREDITS, type TopUpStatus } from "../../api/credits"
import { Button } from "../../ui/Button"
import { creditsCopy } from "./creditsCopy"

type CreditsTopUpCardProps = {
  status: TopUpStatus
  amount: number | null
  balance: number | null
  onTopUp: () => void
}

export function CreditsTopUpCard({ status, amount, balance, onTopUp }: CreditsTopUpCardProps) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-2xl border border-border bg-surface px-6 py-5">
      <h2 className="text-xl text-text">{creditsCopy.topup.title}</h2>
      <p className="text-sm text-muted">{creditsCopy.topup.description}</p>
      <Button onClick={onTopUp} isLoading={status === "pending"}>
        {creditsCopy.topup.action(TOP_UP_CREDITS)}
      </Button>
      {status === "pending" && (
        <p role="status" className="text-sm text-muted">
          {creditsCopy.topup.pending}
        </p>
      )}
      {status === "done" && (
        <p role="status" className="text-sm text-muted">
          {creditsCopy.topup.done(amount ?? TOP_UP_CREDITS, balance ?? 0)}
        </p>
      )}
      {status === "error" && (
        <div role="alert" className="flex flex-col items-start gap-2">
          <p className="text-sm text-red-400">{creditsCopy.topup.error}</p>
          <Button variant="secondary" onClick={onTopUp}>
            {creditsCopy.topup.retry}
          </Button>
        </div>
      )}
    </div>
  )
}
