import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "../../api/client"
import type { components } from "../../api/generated/schema"

type User = components["schemas"]["UserResponse"]
type SessionStatus = "loading" | "signed-out" | "signed-in"

export type SessionContextValue = {
  status: SessionStatus
  user: User | null
  startGuestSession: () => Promise<boolean>
}

async function requestGuest(
  setUser: (user: User) => void,
  setStatus: (status: SessionStatus) => void,
): Promise<boolean> {
  const { data, error } = await apiClient.POST("/api/v1/auth/guest")
  if (error || !data) return false
  setUser(data)
  setStatus("signed-in")
  return true
}

export function useSession(): SessionContextValue {
  const [status, setStatus] = useState<SessionStatus>("loading")
  const [user, setUser] = useState<User | null>(null)

  const loadCurrentUser = useCallback(async () => {
    const { data, response } = await apiClient.GET("/api/v1/me")
    if (response.status === 401 || !data) {
      setUser(null)
      setStatus("signed-out")
      return
    }
    setUser(data)
    setStatus("signed-in")
  }, [])

  useEffect(() => {
    void loadCurrentUser()
  }, [loadCurrentUser])

  // Every hook's runner and the guest button call this; one shared request stops two guests
  // being minted at once, which left a job owned by a guest whose cookie was then overwritten.
  const pendingGuestRef = useRef<Promise<boolean> | null>(null)
  const isSignedInRef = useRef(false)
  isSignedInRef.current = status === "signed-in"
  const startGuestSession = useCallback((): Promise<boolean> => {
    if (isSignedInRef.current) return Promise.resolve(true)
    if (pendingGuestRef.current === null) {
      pendingGuestRef.current = requestGuest(setUser, setStatus).finally(() => {
        pendingGuestRef.current = null
      })
    }
    return pendingGuestRef.current
  }, [])

  return { status, user, startGuestSession }
}
