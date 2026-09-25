import { useEffect, useRef } from "react"
import { useCreditBalance } from "../../api/credits"
import type { GuestSessionSource } from "../../api/guestSession"
import { useCreditsPopover } from "../../ui/useCreditsPopover"
import { CreditsPopoverPanel } from "./CreditsPopoverPanel"

type CreditsButtonProps = {
  session: GuestSessionSource
}

const PANEL_CLASSES =
  "absolute right-0 top-full z-30 mt-2 w-80 rounded-xl border border-border bg-surface p-4 " +
  "shadow-[0_12px_32px_-12px_rgb(28_25_23_/_0.18)]"

function useOutsideClose(rootRef: React.RefObject<HTMLDivElement | null>, close: () => void) {
  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) close()
    }
    document.addEventListener("pointerdown", onPointerDown)
    return () => document.removeEventListener("pointerdown", onPointerDown)
  }, [rootRef, close])
}

function PopoverSurface({ session, onClose }: { session: GuestSessionSource; onClose: () => void }) {
  const rootRef = useRef<HTMLDivElement>(null)
  useOutsideClose(rootRef, onClose)
  return (
    <div ref={rootRef} role="dialog" aria-label="Credits" className={PANEL_CLASSES}>
      <CreditsPopoverPanel session={session} />
    </div>
  )
}

export function CreditsButton({ session }: CreditsButtonProps) {
  const { isOpen, openCredits, closeCredits } = useCreditsPopover()
  const balance = useCreditBalance(session)

  if (session.status !== "signed-in") return null

  return (
    <div
      className="relative"
      onKeyDown={(event) => {
        if (event.key === "Escape") closeCredits()
      }}
    >
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => (isOpen ? closeCredits() : openCredits())}
        className="rounded-md px-2 py-1 font-mono text-[13px] text-text transition-colors hover:text-accent"
      >
        {balance.status === "known" && balance.balance !== null
          ? `${balance.balance} credits`
          : "\u2026"}
      </button>
      {isOpen && <PopoverSurface session={session} onClose={closeCredits} />}
    </div>
  )
}
