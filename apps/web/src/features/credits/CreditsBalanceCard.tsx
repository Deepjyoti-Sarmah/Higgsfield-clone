import type { BalanceStatus } from "../../api/credits"
import { Button } from "../../ui/Button"
import { EmptyState } from "../../ui/EmptyState"
import { creditsCopy } from "./creditsCopy"

type CreditsBalanceCardProps = {
  status: BalanceStatus
  balance: number | null
  onRetry: () => void
}

const cardClasses = "rounded-2xl border border-border bg-surface px-6 py-5"

function LoadingBalance() {
  return (
    <div aria-busy="true" className={cardClasses}>
      <p className="sr-only">{creditsCopy.states.loading.srText}</p>
      <p className="text-sm text-muted">{creditsCopy.balance.label}</p>
      <div className="mt-1 h-9 w-40 animate-pulse rounded bg-border" />
    </div>
  )
}

export function CreditsBalanceCard({ status, balance, onRetry }: CreditsBalanceCardProps) {
  if (status === "error") {
    const { error } = creditsCopy.states
    return (
      <EmptyState
        title={error.title}
        description={error.body}
        action={<Button onClick={onRetry}>{error.action}</Button>}
      />
    )
  }

  if (status === "known" && balance !== null) {
    return (
      <div className={cardClasses}>
        <p className="text-sm text-muted">{creditsCopy.balance.label}</p>
        <p className="mt-1 text-3xl text-text">{creditsCopy.balance.value(balance)}</p>
      </div>
    )
  }

  return <LoadingBalance />
}
