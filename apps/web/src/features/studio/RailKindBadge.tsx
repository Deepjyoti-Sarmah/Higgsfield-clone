import type { LibraryItem } from "../../api/library"

const KIND_LABEL: Record<LibraryItem["kind"], string> = {
  image: "Still",
  video: "Clip",
  sequence: "Sequence",
  faceswap: "Swap",
  video_faceswap: "Swap",
}

type RailKindBadgeProps = {
  kind: LibraryItem["kind"]
}

export function RailKindBadge({ kind }: RailKindBadgeProps) {
  return (
    <span className="shrink-0 rounded border border-border bg-sunken px-1.5 font-mono text-[10px] leading-4 uppercase tracking-wide text-muted">
      {KIND_LABEL[kind] ?? kind}
    </span>
  )
}
