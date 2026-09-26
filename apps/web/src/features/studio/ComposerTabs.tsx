import { ClipComposer } from "../create-video/ClipComposer"
import { FaceSwapComposer } from "../face-swap/FaceSwapComposer"
import { StillComposer } from "../image-create/StillComposer"
import { SequenceComposer } from "../sequence/SequenceComposer"
import { ComposerExplainer } from "./ComposerExplainer"
import { StudioFlowStrip } from "./StudioFlowStrip"
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
  onFaceSwapClip?: (item: LibraryItem) => void
  sequence: SequenceDraftControls
  libraryItems: LibraryItem[]
}

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
        onTabChange={props.onTabChange}
        onFaceSwapClip={props.onFaceSwapClip}
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
      <StudioFlowStrip activeTab={props.tab} onTabChange={props.onTabChange} />
      <ComposerExplainer tab={props.tab} />
      <ActiveComposer {...props} />
    </section>
  )
}
