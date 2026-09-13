import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"

export type PublicJob = components["schemas"]["PublicJobResponse"]

export type PublicJobState = {
  status: "loading" | "ready" | "notFound" | "error"
  job: PublicJob | null
  reload: () => void
}

type PublicJobOutcome =
  | { kind: "ready"; job: PublicJob }
  | { kind: "notFound" }
  | { kind: "error" }

async function fetchPublicJob(jobId: string): Promise<PublicJobOutcome> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/public/jobs/{job_id}", {
      params: { path: { job_id: jobId } },
    })
    if (response.status === 404) return { kind: "notFound" }
    if (response.status !== 200 || !data) return { kind: "error" }
    return { kind: "ready", job: data }
  } catch {
    return { kind: "error" }
  }
}

export function usePublicJob(jobId: string | undefined): PublicJobState {
  const [job, setJob] = useState<PublicJob | null>(null)
  const [status, setStatus] = useState<PublicJobState["status"]>(
    jobId === undefined ? "notFound" : "loading",
  )
  const hasJobRef = useRef(false)
  const isMountedRef = useRef(true)
  const requestIdRef = useRef(0)

  const reload = useCallback(() => {
    if (jobId === undefined) {
      setJob(null)
      setStatus("notFound")
      return
    }
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    if (!hasJobRef.current) setStatus("loading")
    void fetchPublicJob(jobId).then((outcome) => {
      if (!isMountedRef.current || requestId !== requestIdRef.current) return
      const isReady = outcome.kind === "ready"
      if (isReady) hasJobRef.current = true
      setJob(isReady ? outcome.job : null)
      setStatus(outcome.kind)
    })
  }, [jobId])

  useEffect(() => {
    isMountedRef.current = true
    // A new id is a new resource, so its first fetch may show the skeleton again.
    hasJobRef.current = false
    reload()
    return () => {
      isMountedRef.current = false
    }
  }, [reload])

  return { status, job, reload }
}
