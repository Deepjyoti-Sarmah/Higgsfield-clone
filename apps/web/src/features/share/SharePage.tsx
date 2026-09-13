import { useEffect } from "react"
import { useParams } from "react-router-dom"
import { usePublicJob, type PublicJob, type PublicJobState } from "../../api/share"
import { ShareResult } from "./ShareResult"
import { shareCopy } from "./shareCopy"
import { ShareStates, type ShareStateKind } from "./ShareStates"

function useDocumentTitle(presetName: string | null): void {
  // shareCopy has no base app title, so the title from before the share page is restored on unmount.
  useEffect(() => {
    if (presetName === null) return
    const previousTitle = document.title
    document.title = shareCopy.page.documentTitle(presetName)
    return () => {
      document.title = previousTitle
    }
  }, [presetName])
}

function resolveState(status: PublicJobState["status"], job: PublicJob | null): ShareStateKind {
  if (status === "loading") return "loading"
  if (status === "notFound") return "notFound"
  if (job === null) return "error"
  return job.status === "failed" ? "failed" : "notReady"
}

export function SharePage() {
  const { jobId } = useParams<{ jobId: string }>()
  const { status, job, reload } = usePublicJob(jobId)
  useDocumentTitle(job === null ? null : job.preset_name)

  if (status === "ready" && job !== null && job.status === "succeeded") {
    return <ShareResult job={job} />
  }
  return <ShareStates state={resolveState(status, job)} onRetry={reload} />
}
