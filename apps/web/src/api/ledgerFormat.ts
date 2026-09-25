import type { LedgerEntry } from "./ledger"

// Kind labels per the brief: Hold / Settled / Refund / Top-up / Welcome grant.
const KIND_LABELS: Record<LedgerEntry["kind"], string> = {
  HOLD: "Hold",
  SETTLE: "Settled",
  RELEASE: "Refund",
  TOPUP: "Top-up",
  GRANT: "Welcome grant",
}

export function ledgerKindLabel(kind: LedgerEntry["kind"]): string {
  return KIND_LABELS[kind] ?? kind
}

// −20 for holds, +20 for refunds and top-ups, 0 muted for settles of zero.
export function ledgerAmount(amount: number): string {
  if (amount < 0) return `\u2212${Math.abs(amount)}`
  if (amount > 0) return `+${amount}`
  return "0"
}

export function ledgerAmountTone(amount: number): "success" | "text" | "muted" {
  if (amount > 0) return "success"
  if (amount < 0) return "text"
  return "muted"
}

export function relativeTime(iso: string, now: Date = new Date()): string {
  const timestamp = Date.parse(iso)
  if (Number.isNaN(timestamp)) return ""
  const seconds = Math.max(0, Math.round((now.getTime() - timestamp) / 1000))
  if (seconds < 60) return "just now"
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  return `${days}d ago`
}
