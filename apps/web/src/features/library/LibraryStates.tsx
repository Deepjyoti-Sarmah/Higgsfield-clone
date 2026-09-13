import type { ReactNode } from "react"
import { Button } from "../../ui/Button"
import { EmptyState } from "../../ui/EmptyState"
import { libraryCopy } from "./libraryCopy"

type LibraryStatesProps = {
  status: "loading" | "error" | "empty"
  onRetry: () => void
  emptyAction: ReactNode
}

function SkeletonRow() {
  return (
    <li>
      <div className="flex items-center gap-4 rounded-2xl border border-border bg-surface p-3">
        <div className="aspect-[4/3] w-28 shrink-0 animate-pulse rounded-xl bg-border" />
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="h-3 w-1/3 animate-pulse rounded bg-border" />
          <div className="h-3 w-1/4 animate-pulse rounded bg-border" />
          <div className="h-3 w-1/5 animate-pulse rounded bg-border" />
        </div>
      </div>
    </li>
  )
}

function SkeletonRows({ count }: { count: number }) {
  const rows = Array.from({ length: count }, (_, index) => <SkeletonRow key={index} />)
  return <ul className="flex flex-col gap-3">{rows}</ul>
}

export function LibraryStates({ status, onRetry, emptyAction }: LibraryStatesProps) {
  const { loading, error, empty } = libraryCopy.states

  if (status === "loading") {
    return (
      <div aria-busy="true" className="flex flex-col gap-3">
        <p className="sr-only">{loading.srText}</p>
        <SkeletonRows count={loading.skeletonCount} />
      </div>
    )
  }

  if (status === "error") {
    return (
      <EmptyState
        title={error.title}
        description={error.body}
        action={<Button onClick={onRetry}>{error.action}</Button>}
      />
    )
  }

  return <EmptyState title={empty.title} description={empty.body} action={emptyAction} />
}
