import type { PresetCategory } from "../../api/presets"
import { Button } from "../../ui/Button"
import { EmptyState } from "../../ui/EmptyState"
import { exploreCopy } from "./exploreCopy"

type PresetGalleryStatesProps = {
  status: "loading" | "error" | "empty"
  onRetry: () => void
}

type LoadingCategory = {
  key: string
  label: string
  tileKeys: number[]
}

function buildLoadingCategories(tileCount: number): LoadingCategory[] {
  const keys = Object.keys(exploreCopy.gallery.categoryLabels) as PresetCategory[]
  const perCategory = Math.max(1, Math.ceil(tileCount / keys.length))
  return keys.map((key) => ({
    key,
    label: exploreCopy.gallery.categoryLabel(key),
    tileKeys: Array.from({ length: perCategory }, (_, index) => index),
  }))
}

function SkeletonTile() {
  return (
    <li>
      <div className="flex flex-col gap-3 rounded-2xl border border-border bg-surface p-4">
        <div className="aspect-[4/3] animate-pulse rounded-xl bg-border" />
        <div className="h-3 w-2/3 animate-pulse rounded bg-border" />
        <div className="h-3 w-1/3 animate-pulse rounded bg-border" />
      </div>
    </li>
  )
}

export function PresetGalleryStates({ status, onRetry }: PresetGalleryStatesProps) {
  const { loading, error, empty } = exploreCopy.states

  if (status === "loading") {
    return (
      <div aria-busy="true" className="mt-10 space-y-10">
        <p className="sr-only">{loading.srText}</p>
        {buildLoadingCategories(loading.skeletonCount).map((category) => (
          <section key={category.key}>
            <h2 className="text-lg">{category.label}</h2>
            <ul className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {category.tileKeys.map((tileKey) => (
                <SkeletonTile key={tileKey} />
              ))}
            </ul>
          </section>
        ))}
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

  return <EmptyState title={empty.title} description={empty.body} />
}
