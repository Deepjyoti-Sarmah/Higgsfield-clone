import { ClipComposer } from "../create-video/ClipComposer"
import { FaceSwapComposer } from "../face-swap/FaceSwapComposer"
import { StillComposer } from "../image-create/StillComposer"
import { SequenceComposer } from "../sequence/SequenceComposer"
import { Tabs } from "../../ui/Tabs"
import type {
  ComposerProps,
  FaceSwapSeed,
  SeedImage,
  SequenceDraftControls,
  StudioTab,
} from "../../api/studioContracts"
import type { LibraryItem } from "../../api/library"

type ComposerTabsProps = ComposerProps & {
  tab: StudioTab
  onTabChange: (tab: StudioTab) => void
  seedImage: SeedImage | null
  onSeedConsumed: () => void
  seedTarget: FaceSwapSeed | null
  onSeedTargetConsumed: () => void
  sequence: SequenceDraftControls
  libraryItems: LibraryItem[]
}

const TAB_ITEMS = [
  { value: "still", label: "Still" },
  { value: "clip", label: "Clip" },
  { value: "sequence", label: "Sequence" },
  { value: "faceswap", label: "Face swap" },
] as const

function ActiveComposer(props: ComposerTabsProps) {
  if (props.tab === "still") return <StillComposer onJobStarted={props.onJobStarted} />
  if (props.tab === "clip") {
    return (
      <ClipComposer
        onJobStarted={props.onJobStarted}
        seedImage={props.seedImage}
        onSeedConsumed={props.onSeedConsumed}
      />
    )
  }
  if (props.tab === "sequence") {
    return (
      <SequenceComposer
        onJobStarted={props.onJobStarted}
        sequence={props.sequence}
        libraryItems={props.libraryItems}
      />
    )
  }
  return (
    <FaceSwapComposer
      onJobStarted={props.onJobStarted}
      seedTarget={props.seedTarget}
      onSeedConsumed={props.onSeedTargetConsumed}
    />
  )
}

export function ComposerTabs(props: ComposerTabsProps) {
  return (
    <section aria-label="Composer" className="border-t border-border bg-surface">
      <div className="px-4 pt-2 sm:px-6">
        <Tabs items={TAB_ITEMS} value={props.tab} onChange={props.onTabChange} ariaLabel="Composer tabs" />
      </div>
      <ActiveComposer {...props} />
    </section>
  )
}
