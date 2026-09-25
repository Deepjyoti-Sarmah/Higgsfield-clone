import { useContext } from "react"
import { CreditsPopoverContext } from "./creditsPopoverContext"

export function useCreditsPopover() {
  const value = useContext(CreditsPopoverContext)
  if (value === null) throw new Error("useCreditsPopover needs CreditsPopoverProvider")
  return value
}
