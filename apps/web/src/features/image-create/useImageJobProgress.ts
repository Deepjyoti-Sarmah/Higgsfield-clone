import { fetchImageJob } from "../../api/imageJobHelpers"
import type { ImageJob } from "../../api/imageJobHelpers"
import { useJobEvents } from "../../api/useJobEvents"
import type { JobWatch } from "../../api/useJobEvents"

// Parallel to useImageJob's own watcher (api/imageJobs.ts is off-limits): that one only
// surfaces the job on the initial/final fetch, never a live "running" transition. Reuses
// the same jobStatusWatcher + fetchImageJob purely for progress; useImageJob owns the result.
export function useImageJobProgress(jobId: string | null): JobWatch<ImageJob> {
  return useJobEvents<ImageJob>(jobId, fetchImageJob)
}
