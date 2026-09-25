import { ClipComposer } from "../create-video/ClipComposer"
import { StillComposer } from "../image-create/StillComposer"
import { SequenceComposer } from "../sequence/SequenceComposer"
import { Tabs } from "../../ui/Tabs"
import type {
  ComposerProps,
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
  sequence: SequenceDraftControls
  libraryItems: LibraryItem[]
}

const TAB_ITEMS = [
  { value: "still", label: "Still" },
  { value: "clip", label: "Clip" },
  { value: "sequence", label: "Sequence" },
] as const

export function ComposerTabs({
  tab,
  onTabChange,
  onJobStarted,
  seedImage,
  onSeedConsumed,
  sequence,
  libraryItems,
}: ComposerTabsProps) {
  return (
    <section aria-label="Composer" className="border-t border-border bg-surface">
      <div className="px-4 pt-2 sm:px-6">
        <Tabs items={TAB_ITEMS} value={tab} onChange={onTabChange} ariaLabel="Composer tabs" />
      </div>
      {tab === "still" && <StillComposer onJobStarted={onJobStarted} />}
      {tab === "clip" && (
        <ClipComposer
          onJobStarted={onJobStarted}
          seedImage={seedImage}
          onSeedConsumed={onSeedConsumed}
        />
      )}
      {tab === "sequence" && (
        <SequenceComposer
          onJobStarted={onJobStarted}
          sequence={sequence}
          libraryItems={libraryItems}
        />
      )}
    </section>
  )
}
