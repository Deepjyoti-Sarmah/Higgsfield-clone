import { Navigate, Route, Routes, useLocation } from "react-router-dom"
import { AppShell } from "./ui/AppShell"
import { CreditsPopoverProvider } from "./ui/CreditsPopoverContext"
import { CreditsButton } from "./features/credits/CreditsButton"
import { GuestButton } from "./features/session/GuestButton"
import { SessionBadge } from "./features/session/SessionBadge"
import { useSession } from "./features/session/useSession"
import { SharePage } from "./features/share/SharePage"
import { StartPage } from "./features/start/StartPage"
import { StudioPage } from "./features/studio/StudioPage"

// Redirects keep every query param; /library's ?job= is renamed ?item= (AC-6).
function LibraryRedirect() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const job = params.get("job")
  params.delete("job")
  if (job !== null) params.set("item", job)
  const search = params.toString()
  return <Navigate to={`/studio${search ? `?${search}` : ""}`} replace />
}

function StudioRedirect({ tab }: { tab: "clip" | "still" }) {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  params.set("tab", tab)
  return <Navigate to={`/studio?${params.toString()}`} replace />
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
    <CreditsPopoverProvider>
      <Routes>
        <Route
          element={<AppShell rightSlot={rightSlot} creditsSlot={<CreditsButton session={session} />} outletContext={session} />}
        >
          <Route index element={<StartPage />} />
          <Route path="studio" element={<StudioPage />} />
          <Route path="create/video" element={<StudioRedirect tab="clip" />} />
          <Route path="create/image" element={<StudioRedirect tab="still" />} />
          <Route path="library" element={<LibraryRedirect />} />
          <Route path="credits" element={<Navigate to="/studio?credits=open" replace />} />
          <Route path="v/:jobId" element={<SharePage />} />
        </Route>
      </Routes>
    </CreditsPopoverProvider>
  )
}
