import { useOutletContext } from "react-router-dom"
import { useLibrary } from "../../api/library"
import type { LibraryState } from "../../api/library"
import { ButtonLink } from "../../ui/ButtonLink"
import type { SessionContextValue } from "../session/useSession"
import { libraryCopy } from "./libraryCopy"
import { LibraryList } from "./LibraryList"
import { LibraryResultView } from "./LibraryResultView"
import { LibraryStates } from "./LibraryStates"
import { useLibraryJobParam } from "./useLibraryJobParam"

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

  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-8 py-4">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-text">{libraryCopy.page.title}</h1>
        <p className="text-muted">{libraryCopy.page.subtitle}</p>
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
      {isResultOpen && <LibraryResultView item={selectedItem} />}
    </section>
  )
}
