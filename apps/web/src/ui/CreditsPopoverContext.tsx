import { useCallback, useMemo, useState, type ReactNode } from "react"
import { CreditsPopoverContext } from "./creditsPopoverContext"

export function CreditsPopoverProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const openCredits = useCallback(() => setIsOpen(true), [])
  const closeCredits = useCallback(() => setIsOpen(false), [])
  const value = useMemo(
    () => ({ isOpen, openCredits, closeCredits }),
    [isOpen, openCredits, closeCredits],
  )
  return <CreditsPopoverContext.Provider value={value}>{children}</CreditsPopoverContext.Provider>
}
