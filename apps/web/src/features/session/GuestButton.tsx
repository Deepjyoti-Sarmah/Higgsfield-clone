import { useState } from "react"
import { Button } from "../../ui/Button"

type GuestButtonProps = {
  startGuestSession: () => Promise<boolean>
}

type GuestButtonState = "idle" | "loading" | "error"

export function GuestButton({ startGuestSession }: GuestButtonProps) {
  const [state, setState] = useState<GuestButtonState>("idle")

  async function handleClick() {
    setState("loading")
    const didSucceed = await startGuestSession()
    setState(didSucceed ? "idle" : "error")
  }

  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        variant="primary"
        isLoading={state === "loading"}
        onClick={() => void handleClick()}
      >
        Continue as guest
      </Button>
      {state === "error" && (
        <p className="text-sm text-red-400">
          Couldn't start a session. Try again.
        </p>
      )}
    </div>
  )
}
