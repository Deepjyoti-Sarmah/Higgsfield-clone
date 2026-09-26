import { announceCreditsChanged } from "../../api/creditsSignal"
import { useCallback, useEffect, useState } from "react"
import { useOutletContext } from "react-router-dom"
import type { LibraryItem } from "../../api/library"
import { useLibrary } from "../../api/library"
import type { SessionContextValue } from "../session/useSession"
import type { FaceSwapSeed, SeedImage, StudioTab } from "../../api/studioContracts"
import { useSequenceDraft } from "./useSequenceDraft"
import { MAX_SEQUENCE_CLIPS } from "./draftOps"
import { DEFAULT_CLIP_DURATION_MS } from "../sequence/sequenceDraftView"
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
  const values: StudioTab[] = ["still", "clip", "sequence", "faceswap"]
  return values.includes(raw as StudioTab) ? (raw as StudioTab) : "still"
}

function useStudioActions(library: ReturnType<typeof useLibrary>) {
  const { searchParams, setParam } = useStudioParams()
  const [seedImage, setSeedImage] = useState<SeedImage | null>(null)
  const [seedTarget, setSeedTarget] = useState<FaceSwapSeed | null>(null)
  const selectItem = useCallback((jobId: string) => setParam("item", jobId), [setParam])
  const changeTab = useCallback((next: StudioTab) => setParam("tab", next), [setParam])
  const onJobStarted = useCallback((jobId: string) => {
    library.reloadLibrary()
    announceCreditsChanged()
    selectItem(jobId)
  }, [library, selectItem])
  const onAnimateThis = useCallback((_item: LibraryItem, url: string, assetId: string) => {
    setSeedImage({ assetId, url })
    changeTab("clip")
  }, [changeTab])
  const onUseAsFaceSwapTarget = useCallback((url: string, assetId: string) => {
    setSeedTarget({ assetId, url })
    changeTab("faceswap")
  }, [changeTab])
  const consumeSeed = useCallback(() => setSeedImage(null), [])
  const consumeSeedTarget = useCallback(() => setSeedTarget(null), [])
  return {
    searchParams,
    selectItem,
    changeTab,
    onJobStarted,
    onAnimateThis,
    onUseAsFaceSwapTarget,
    seedImage,
    consumeSeed,
    seedTarget,
    consumeSeedTarget,
  }
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
) {
  return (
    <ComposerTabs
      tab={readTab(actions.searchParams.get("tab"))}
      onTabChange={actions.changeTab}
      onJobStarted={actions.onJobStarted}
      seedImage={actions.seedImage}
      onSeedConsumed={actions.consumeSeed}
      seedTarget={actions.seedTarget}
      onSeedTargetConsumed={actions.consumeSeedTarget}
      sequence={draft}
      libraryItems={items}
    />
  )
}

// Backstop: the terminal transition normally comes from the job watcher's
// SSE/poll callback, but a dropped event (e.g. the per-origin EventSource
// cap) would otherwise leave StageActions stuck on a stale snapshot.
function useLibraryHealPoll(selectedItem: LibraryItem | null, reloadLibrary: () => void) {
  const isSelectedItemLive = selectedItem?.status === "queued" || selectedItem?.status === "running"
  useEffect(() => {
    if (!isSelectedItemLive) return
    const timer = window.setInterval(reloadLibrary, 5000)
    return () => window.clearInterval(timer)
  }, [isSelectedItemLive, reloadLibrary])
}

function useStudioPanel(props: {
  library: ReturnType<typeof useLibrary>
  actions: ReturnType<typeof useStudioActions>
  draft: ReturnType<typeof useSequenceDraft>
}) {
  const { library, actions, draft } = props
  const selectedId = actions.searchParams.get("item")

  const onAddToSequence = useCallback((item: LibraryItem) => {
    const accepted = draft.addClip({
      jobId: item.id,
      posterUrl: item.thumbnail_url,
      aspect: null,
      durationMs: item.duration_ms ?? DEFAULT_CLIP_DURATION_MS,
    })
    if (!accepted) window.alert(`Sequence is full (${MAX_SEQUENCE_CLIPS} clips).`)
  }, [draft])

  const { reloadLibrary } = library
  const onJobSettled = useCallback(() => {
    reloadLibrary()
    announceCreditsChanged()
  }, [reloadLibrary])
  const selectedItem = library.items.find((item) => item.id === selectedId) ?? null
  useLibraryHealPoll(selectedItem, reloadLibrary)
  const rail = buildRail(library, selectedId, actions)
  const stage = (
    <StudioStage
      item={selectedItem}
      liveStatus={selectedItem?.status ?? null}
      sequenceFull={draft.draft.clips.length >= MAX_SEQUENCE_CLIPS}
      onAnimateThis={actions.onAnimateThis}
      onAddToSequence={onAddToSequence}
      onUseAsFaceSwapTarget={actions.onUseAsFaceSwapTarget}
      onJobSettled={onJobSettled}
    />
  )
  const composer = buildComposer(actions, draft, library.items)
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
