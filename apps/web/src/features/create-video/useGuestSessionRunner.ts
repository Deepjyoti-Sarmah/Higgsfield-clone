import { useCallback, useRef } from "react"
import type { SessionContextValue } from "../session/useSession"
import type { GuestSessionOutcome, RunWithGuestSession } from "./createVideoTypes"

type SessionStatus = SessionContextValue["status"]

export function useGuestSessionRunner(session: SessionContextValue): RunWithGuestSession {
  const statusRef = useRef<SessionStatus>(session.status)
  const startGuestSessionRef = useRef(session.startGuestSession)
  const guestPromiseRef = useRef<Promise<boolean> | null>(null)

  statusRef.current = session.status
  startGuestSessionRef.current = session.startGuestSession

  const ensureGuest = useCallback((): Promise<boolean> => {
    if (!guestPromiseRef.current) {
      const pending = startGuestSessionRef.current().finally(() => {
        guestPromiseRef.current = null
      })
      guestPromiseRef.current = pending
    }
    return guestPromiseRef.current
  }, [])

  return useCallback(
    async <T extends { response: Response }>(
      request: () => Promise<T>,
    ): Promise<GuestSessionOutcome<T>> => {
      if (statusRef.current === "signed-out" && !(await ensureGuest())) {
        return { outcome: "session-failed" }
      }
      const first = await request()
      if (first.response.status !== 401) {
        return { outcome: "done", result: first }
      }
      if (!(await ensureGuest())) {
        return { outcome: "session-failed" }
      }
      return { outcome: "done", result: await request() }
    },
    [ensureGuest],
  )
}
