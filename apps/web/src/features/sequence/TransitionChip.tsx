import type { SequenceTransition } from "../../api/studioContracts"
import { nextTransition } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"

type TransitionChipProps = {
  position: number
  transition: SequenceTransition
  onCycle: (next: SequenceTransition) => void
}

export function TransitionChip({ position, transition, onCycle }: TransitionChipProps) {
  const copy = sequenceCopy.transitions[transition]
  return (
    <button
      type="button"
      onClick={() => onCycle(nextTransition(transition))}
      aria-label={`Transition before shot ${position + 1}: ${copy.name}`}
      className="h-6 shrink-0 rounded-full border border-border bg-surface px-2 font-mono text-[10px] tracking-wide text-muted transition-colors hover:border-accent/60 hover:text-text"
    >
      {copy.label}
    </button>
  )
}
