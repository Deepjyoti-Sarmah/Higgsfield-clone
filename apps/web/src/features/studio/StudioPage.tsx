import { useCallback, useState } from "react"
import { useOutletContext } from "react-router-dom"
import type { LibraryItem } from "../../api/library"
import { useLibrary } from "../../api/library"
import type { SessionContextValue } from "../session/useSession"
import type { SeedImage, StudioTab } from "../../api/studioContracts"
import { useSequenceDraft } from "./useSequenceDraft"
import { MAX_SEQUENCE_CLIPS } from "./draftOps"
import { StudioRail } from "./StudioRail"
import { StudioStage } from "./StudioStage"
import { ComposerTabs } from "./ComposerTabs"
import { useStudioParams } from "./useStudioParams"
import { useLibraryDrawer } from "./useLibraryDrawer"
import { RailDrawer } from "./RailDrawer"

function useOutletSession(): SessionContextValue {
  return useOutletContext<SessionContextValue>()
}

function MobileLibraryBar({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="flex items-center gap-2 border-b border-border px-4 py-2 lg:hidden">
      <button
        type="button"
        onClick={onOpen}
        className="h-10 rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text"
      >
        Library
      </button>
    </div>
  )
}

function readTab(raw: string | null): StudioTab {
  const values: StudioTab[] = ["still", "clip", "sequence"]
  return values.includes(raw as StudioTab) ? (raw as StudioTab) : "still"
}

function useStudioActions(library: ReturnType<typeof useLibrary>) {
  const { searchParams, setParam } = useStudioParams()
  const [seedImage, setSeedImage] = useState<SeedImage | null>(null)
  const selectItem = useCallback((jobId: string) => setParam("item", jobId), [setParam])
  const changeTab = useCallback((next: StudioTab) => setParam("tab", next), [setParam])
  const onJobStarted = useCallback((jobId: string) => {
    library.reloadLibrary()
    selectItem(jobId)
  }, [library, selectItem])
  const onAnimateThis = useCallback((_item: LibraryItem, url: string, assetId: string) => {
    setSeedImage({ assetId, url })
    changeTab("clip")
  }, [changeTab])
  const consumeSeed = useCallback(() => setSeedImage(null), [])
  return { searchParams, selectItem, changeTab, onJobStarted, onAnimateThis, seedImage, consumeSeed }
}

function buildRail(
  library: ReturnType<typeof useLibrary>,
  selectedId: string | null,
  actions: ReturnType<typeof useStudioActions>,
) {
  return (
    <StudioRail
      library={library}
      selectedId={selectedId}
      onSelect={actions.selectItem}
      onOpenStudioComposer={() => actions.changeTab("still")}
    />
  )
}

function buildComposer(
  actions: ReturnType<typeof useStudioActions>,
  draft: ReturnType<typeof useSequenceDraft>,
  items: LibraryItem[],
  onSeedConsumed: () => void,
) {
  return (
    <ComposerTabs
      tab={readTab(actions.searchParams.get("tab"))}
      onTabChange={actions.changeTab}
      onJobStarted={actions.onJobStarted}
      seedImage={actions.seedImage}
      onSeedConsumed={onSeedConsumed}
      sequence={draft}
      libraryItems={items}
    />
  )
}

function useStudioPanel(props: {
  library: ReturnType<typeof useLibrary>
  actions: ReturnType<typeof useStudioActions>
  draft: ReturnType<typeof useSequenceDraft>
}) {
  const { library, actions, draft } = props
  const selectedId = actions.searchParams.get("item")

  const onAddToSequence = useCallback((item: LibraryItem) => {
    const accepted = draft.addClip({ jobId: item.id, posterUrl: item.thumbnail_url, aspect: null })
    if (!accepted) window.alert(`Sequence is full (${MAX_SEQUENCE_CLIPS} clips).`)
  }, [draft])

  const selectedItem = library.items.find((item) => item.id === selectedId) ?? null
  const rail = buildRail(library, selectedId, actions)
  const stage = (
    <StudioStage
      item={selectedItem}
      liveStatus={selectedItem?.status ?? null}
      sequenceFull={draft.draft.clips.length >= MAX_SEQUENCE_CLIPS}
      onAnimateThis={actions.onAnimateThis}
      onAddToSequence={onAddToSequence}
      onJobSettled={library.reloadLibrary}
    />
  )
  const composer = buildComposer(actions, draft, library.items, actions.consumeSeed)
  return { rail, stage, composer }
}

export function StudioPage() {
  const session = useOutletSession()
  const library = useLibrary(session)
  const actions = useStudioActions(library)
  const draft = useSequenceDraft()
  const drawer = useLibraryDrawer()
  const { rail, stage, composer } = useStudioPanel({ library, actions, draft })

  return (
    <div className="grid min-h-[calc(100dvh-3.5rem-2.5rem)] grid-rows-[1fr_auto] max-lg:grid-cols-1 lg:grid-cols-[288px_1fr]">
      <aside className="hidden min-h-0 overflow-y-auto border-r border-border lg:block">{rail}</aside>
      <RailDrawer isOpen={drawer.isDrawerOpen} onClose={drawer.closeDrawer}>{rail}</RailDrawer>
      <div className="flex min-h-0 flex-col">
        <MobileLibraryBar onOpen={drawer.openDrawer} />
        {stage}
        {composer}
      </div>
    </div>
  )
}
