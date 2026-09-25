import type { components } from "../../api/generated/schema"

type User = components["schemas"]["UserResponse"]

type SessionBadgeProps = {
  user: User
}

export function SessionBadge({ user }: SessionBadgeProps) {
  const shortId = user.id.slice(0, 6)
  return (
    <span className="whitespace-nowrap rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-muted">
      Guest<span className="hidden sm:inline"> · {shortId}</span>
    </span>
  )
}
