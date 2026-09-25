import type { ReactNode } from "react"

type RailDrawerProps = {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
}

export function RailDrawer({ isOpen, onClose, children }: RailDrawerProps) {
  if (!isOpen) return null
  return (
    <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Library">
      <button
        type="button"
        aria-label="Close library"
        onClick={onClose}
        className="absolute inset-0 bg-scrim"
      />
      <div className="absolute inset-y-0 left-0 w-72 overflow-y-auto border-r border-border bg-surface">
        {children}
      </div>
    </div>
  )
}
