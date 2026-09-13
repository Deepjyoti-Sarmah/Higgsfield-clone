import { useNavigate, useOutletContext } from "react-router-dom"
import { Button } from "../../ui/Button"
import { GuestButton } from "../session/GuestButton"
import type { SessionContextValue } from "../session/useSession"

export function HomePage() {
  const { status, startGuestSession } = useOutletContext<SessionContextValue>()
  const navigate = useNavigate()

  return (
    <section className="mx-auto flex max-w-2xl flex-col items-center gap-6 py-16 text-center">
      <h1 className="text-4xl sm:text-5xl">Make your next video</h1>
      <p className="max-w-md text-muted">
        Generate video and image content in one click. Start free as a guest,
        no sign-up required.
      </p>
      {status === "signed-in" ? (
        <Button variant="primary" onClick={() => navigate("/create/video")}>
          Create video
        </Button>
      ) : (
        <GuestButton startGuestSession={startGuestSession} />
      )}
    </section>
  )
}
