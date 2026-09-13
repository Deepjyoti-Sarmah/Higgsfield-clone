import { Route, Routes } from "react-router-dom"
import { AppShell } from "./ui/AppShell"
import { CreateVideoPage } from "./features/create-video/CreateVideoPage"
import { CreditsPage } from "./features/credits/CreditsPage"
import { ExplorePage } from "./features/explore/ExplorePage"
import { CreateImagePage } from "./features/image-create/CreateImagePage"
import { LibraryPage } from "./features/library/LibraryPage"
import { GuestButton } from "./features/session/GuestButton"
import { SessionBadge } from "./features/session/SessionBadge"
import { useSession } from "./features/session/useSession"
import { SharePage } from "./features/share/SharePage"

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
        <Route index element={<ExplorePage />} />
        <Route path="create/video" element={<CreateVideoPage />} />
        <Route path="create/image" element={<CreateImagePage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="credits" element={<CreditsPage />} />
        <Route path="v/:jobId" element={<SharePage />} />
      </Route>
    </Routes>
  )
}
