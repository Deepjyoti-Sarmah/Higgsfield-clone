import { createContext } from "react"

export type CreditsPopoverValue = {
  isOpen: boolean
  openCredits: () => void
  closeCredits: () => void
}

export const CreditsPopoverContext = createContext<CreditsPopoverValue | null>(null)
