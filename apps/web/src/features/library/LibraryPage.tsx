import { useEffect, useRef } from "react"
import { useOutletContext } from "react-router-dom"
import { useLibrary } from "../../api/library"
import type { LibraryState } from "../../api/library"
import { usePrefersReducedMotion } from "../create-video/usePrefersReducedMotion"
import { ButtonLink } from "../../ui/ButtonLink"
import type { SessionContextValue } from "../session/useSession"
import { libraryCopy } from "./libraryCopy"
import { LibraryList } from "./LibraryList"
import { LibraryResultView } from "./LibraryResultView"
import { LibraryStates } from "./LibraryStates"
import { useLibraryJobParam } from "./useLibraryJobParam"

function isFullyVisible(node: HTMLElement): boolean {
  const rect = node.getBoundingClientRect()
  return rect.top >= 0 && rect.bottom <= window.innerHeight
}

// Scrolls (and moves focus) to the result panel only on an actual change of selection --
// never on first mount, even with ?job=<id> already in the URL.
function useScrollResultIntoView(selectedJobId: string | null, resultRef: React.RefObject<HTMLDivElement | null>) {
  const prefersReducedMotion = usePrefersReducedMotion()
  const previousJobIdRef = useRef(selectedJobId)

  useEffect(() => {
    const changed = previousJobIdRef.current !== selectedJobId
    previousJobIdRef.current = selectedJobId
    if (!changed || selectedJobId === null) return
    const node = resultRef.current
    if (node === null) return
    if (!isFullyVisible(node)) {
      node.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" })
    }
    node.focus({ preventScroll: true })
  }, [selectedJobId, prefersReducedMotion, resultRef])
}

type LibraryStatesStatus = "loading" | "error" | "empty"

function deriveStatesStatus(state: LibraryState): LibraryStatesStatus | null {
  if (state.status === "loading") return "loading"
  if (state.status === "error") return "error"
  if (state.items.length === 0) return "empty"
  return null
}

export function LibraryPage() {
  const session = useOutletContext<SessionContextValue>()
  const state = useLibrary(session)
  const { selectedJobId, selectedItem, isMissing, selectJob } = useLibraryJobParam(state.items)
  const statesStatus = deriveStatesStatus(state)
  // A `?job=` id can only be called missing once the list has actually loaded.
  const isResultOpen = selectedItem !== null || (isMissing && state.status === "ready")
  const resultRef = useRef<HTMLDivElement>(null)
  useScrollResultIntoView(selectedJobId, resultRef)

  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-8 py-4">
      <header className="flex flex-col gap-2">
        <h1 className="text-4xl leading-none text-text sm:text-5xl">{libraryCopy.page.title}</h1>
        <p className="max-w-xl text-muted">{libraryCopy.page.subtitle}</p>
      </header>
      {statesStatus !== null && (
        <LibraryStates
          status={statesStatus}
          onRetry={state.reloadLibrary}
          emptyAction={<ButtonLink to="/create/video">{libraryCopy.states.empty.action}</ButtonLink>}
        />
      )}
      {state.status === "ready" && state.items.length > 0 && (
        <LibraryList items={state.items} selectedJobId={selectedJobId} onSelect={selectJob} />
      )}
      {isResultOpen && (
        <div ref={resultRef} tabIndex={-1} aria-live="polite" className="outline-none">
          <LibraryResultView item={selectedItem} />
        </div>
      )}
    </section>
  )
}
