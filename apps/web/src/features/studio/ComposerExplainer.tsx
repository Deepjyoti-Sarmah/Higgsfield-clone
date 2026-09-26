import type { StudioTab } from "../../api/studioContracts"
import { studioCopy } from "./studioCopy"

type ComposerExplainerProps = { tab: StudioTab }

export function ComposerExplainer({ tab }: ComposerExplainerProps) {
  const copy = studioCopy.explainer[tab]
  return (
    <div className="px-4 pt-3 sm:px-6" aria-live="polite">
      <p className="text-sm font-semibold text-text">{copy.title}</p>
      <p className="text-xs text-muted">{copy.body}</p>
    </div>
  )
}
