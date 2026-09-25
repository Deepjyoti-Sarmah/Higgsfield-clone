import { useEffect, useRef } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useCreditsPopover } from "../../ui/useCreditsPopover"

// Owns ?tab= and ?item=; ?credits=open opens the popover once, then is removed.
export function useStudioParams() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { openCredits } = useCreditsPopover()
  const creditsHandled = useRef(false)

  useEffect(() => {
    if (searchParams.get("credits") !== "open" || creditsHandled.current) return
    creditsHandled.current = true
    openCredits()
    const next = new URLSearchParams(searchParams)
    next.delete("credits")
    setSearchParams(next, { replace: true })
  }, [searchParams, openCredits, setSearchParams])

  function setParam(name: string, value: string) {
    const next = new URLSearchParams(searchParams)
    next.set(name, value)
    navigate({ pathname: "/studio", search: next.toString() })
  }

  return { searchParams, setParam }
}
