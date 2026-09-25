import { Link } from "react-router-dom"
import type { LedgerEntry } from "../../api/ledger"
import type { LedgerState } from "../../api/ledger"
import { ledgerAmount, ledgerAmountTone, ledgerKindLabel, relativeTime } from "../../api/ledgerFormat"
import { Skeleton } from "../../ui/Skeleton"
import { Button } from "../../ui/Button"

type LedgerListProps = {
  state: LedgerState
}

const TONE_CLASSES = {
  success: "text-success",
  text: "text-text",
  muted: "text-muted",
} as const

function LedgerRow({ entry }: { entry: LedgerEntry }) {
  return (
    <li className="flex items-center justify-between gap-2 py-1.5">
      <div className="flex min-w-0 flex-col">
        <span className="text-[13px] text-text">{ledgerKindLabel(entry.kind)}</span>
        <span className="font-mono text-[11px] text-faint">{relativeTime(entry.created_at)}</span>
      </div>
      {entry.job_id !== null ? (
        <Link
          to={`/studio?item=${entry.job_id}`}
          className="font-mono text-[13px] underline-offset-2 hover:underline"
        >
          <span className={TONE_CLASSES[ledgerAmountTone(entry.amount)]}>
            {ledgerAmount(entry.amount)}
          </span>
        </Link>
      ) : (
        <span className={`font-mono text-[13px] ${TONE_CLASSES[ledgerAmountTone(entry.amount)]}`}>
          {ledgerAmount(entry.amount)}
        </span>
      )}
    </li>
  )
}

export function LedgerList({ state }: LedgerListProps) {
  if (state.status === "loading") {
    return (
      <div className="flex flex-col gap-2 py-1" aria-busy="true">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-8 w-full" label="Loading the ledger" />
        ))}
      </div>
    )
  }
  if (state.status === "error") {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-[13px] text-muted">The ledger didn't load.</p>
        <Button variant="secondary" onClick={state.reload}>
          Retry
        </Button>
      </div>
    )
  }
  if (state.status !== "ready" || state.items.length === 0) {
    return <p className="text-[13px] text-faint">No entries yet.</p>
  }
  return (
    <ul className="divide-y divide-border">
      {state.items.map((entry) => (
        <LedgerRow key={entry.id} entry={entry} />
      ))}
    </ul>
  )
}
