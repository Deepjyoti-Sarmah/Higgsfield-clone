import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
} from "react"
import { isDismissKey } from "./popoverKeys"

type PopoverProps = {
  trigger: (props: { "aria-expanded": boolean; "aria-controls": string; onClick: () => void }) => ReactNode
  children: ReactNode | ((close: () => void) => ReactNode)
}

const PANEL_CLASSES =
  "absolute right-0 top-full z-30 mt-2 w-80 rounded-xl border border-border bg-surface p-4 " +
  "shadow-[0_12px_32px_-12px_rgb(28_25_23_/_0.18)]"

function usePopoverDismiss(
  rootRef: React.RefObject<HTMLElement | null>, isOpen: boolean, close: () => void,
) {
  useEffect(() => {
    if (!isOpen) return
    function handlePointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) close()
    }
    document.addEventListener("pointerdown", handlePointerDown)
    return () => document.removeEventListener("pointerdown", handlePointerDown)
  }, [rootRef, isOpen, close])
}

export function Popover({ trigger, children }: PopoverProps) {
  const [isOpen, setIsOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLElement | null>(null)
  const panelId = useId()

  function close() {
    setIsOpen(false)
    triggerRef.current?.focus()
  }

  usePopoverDismiss(rootRef, isOpen, close)

  function dismiss(event: ReactKeyboardEvent<HTMLElement>) {
    if (isDismissKey(event.key)) close()
  }

  return (
    <div ref={rootRef} className="relative">
      <span
        ref={(node) => {
          triggerRef.current = node
        }}
        onKeyDown={dismiss}
      >
        {trigger({
          "aria-expanded": isOpen,
          "aria-controls": panelId,
          onClick: () => setIsOpen((open) => !open),
        })}
      </span>
      {isOpen && (
        <div id={panelId} role="dialog" aria-modal="false" onKeyDown={dismiss} className={PANEL_CLASSES}>
          {typeof children === "function" ? children(() => setIsOpen(false)) : children}
        </div>
      )}
    </div>
  )
}
