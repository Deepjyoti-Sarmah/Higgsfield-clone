import { useCallback, useEffect, useState } from "react"
import { apiClient } from "../../api/client"
import type { components } from "../../api/generated/schema"

type User = components["schemas"]["UserResponse"]
type SessionStatus = "loading" | "signed-out" | "signed-in"

export type SessionContextValue = {
  status: SessionStatus
  user: User | null
  startGuestSession: () => Promise<boolean>
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

  const startGuestSession = useCallback(async () => {
    const { data, error } = await apiClient.POST("/api/v1/auth/guest")
    if (error || !data) {
      return false
    }
    setUser(data)
    setStatus("signed-in")
    return true
  }, [])

  return { status, user, startGuestSession }
}
