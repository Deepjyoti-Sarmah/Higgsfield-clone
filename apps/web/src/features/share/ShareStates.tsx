import { Button } from "../../ui/Button"
import { ButtonLink } from "../../ui/ButtonLink"
import { EmptyState } from "../../ui/EmptyState"
import { shareCopy } from "./shareCopy"

export type ShareStateKind = "loading" | "error" | "notFound" | "notReady" | "failed"

type ShareStatesProps = {
  state: ShareStateKind
  onRetry: () => void
}

function LoadingSkeleton() {
  return (
    <div
      aria-busy="true"
      className="flex w-full max-w-2xl flex-col items-center gap-4"
    >
      <p className="sr-only">{shareCopy.states.loading.srText}</p>
      <div className="aspect-video w-full animate-pulse rounded-xl border border-border bg-surface" />
    </div>
  )
}

export function ShareStates({ state, onRetry }: ShareStatesProps) {
  if (state === "loading") return <LoadingSkeleton />

  if (state === "error") {
    const { error } = shareCopy.states
    return (
      <EmptyState
        title={error.title}
        description={error.body}
        action={<Button onClick={onRetry}>{error.action}</Button>}
      />
    )
  }

  if (state === "notReady") {
    const { notReady } = shareCopy.states
    return (
      <EmptyState
        title={notReady.title}
        description={notReady.body}
        action={<Button onClick={onRetry}>{notReady.action}</Button>}
      />
    )
  }

  const copy = state === "notFound" ? shareCopy.states.notFound : shareCopy.states.failed
  return (
    <EmptyState
      title={copy.title}
      description={copy.body}
      action={<ButtonLink to={shareCopy.page.ctaHref}>{copy.action}</ButtonLink>}
    />
  )
}
