import { Route, Routes } from "react-router-dom"
import { AppShell } from "./ui/AppShell"
import { EmptyState } from "./ui/EmptyState"
import { CreateVideoPage } from "./features/create-video/CreateVideoPage"
import { HomePage } from "./features/home/HomePage"
import { GuestButton } from "./features/session/GuestButton"
import { SessionBadge } from "./features/session/SessionBadge"
import { useSession } from "./features/session/useSession"

function Placeholder({ title }: { title: string }) {
  return (
    <EmptyState
      title={title}
      description="This part of Higgsfield is coming in a later slice."
    />
  )
}

export function App() {
  const session = useSession()
  const rightSlot =
    session.status === "signed-in" && session.user ? (
      <SessionBadge user={session.user} />
    ) : session.status === "signed-out" ? (
      <GuestButton startGuestSession={session.startGuestSession} />
    ) : null

  return (
    <Routes>
      <Route
        element={<AppShell rightSlot={rightSlot} outletContext={session} />}
      >
        <Route index element={<HomePage />} />
        <Route path="create/video" element={<CreateVideoPage />} />
        <Route
          path="create/image"
          element={<Placeholder title="Create image" />}
        />
        <Route path="library" element={<Placeholder title="Library" />} />
        <Route path="credits" element={<Placeholder title="Credits" />} />
        <Route
          path="v/:jobId"
          element={
            <EmptyState
              title="Share page"
              description="Public share pages are coming soon."
            />
          }
        />
      </Route>
    </Routes>
  )
}
