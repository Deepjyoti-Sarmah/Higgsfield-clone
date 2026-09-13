import { useCallback, useRef } from "react"

export type GuestSessionSource = {
  status: "loading" | "signed-out" | "signed-in"
  startGuestSession: () => Promise<boolean>
}

export type GuestSessionOutcome<T> =
  | { outcome: "done"; result: T }
  | { outcome: "session-failed" }

export type RunWithGuestSession = <T extends { response: Response }>(
  request: () => Promise<T>,
) => Promise<GuestSessionOutcome<T>>

export function useGuestSessionRunner(session: GuestSessionSource): RunWithGuestSession {
  const statusRef = useRef<GuestSessionSource["status"]>(session.status)
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
