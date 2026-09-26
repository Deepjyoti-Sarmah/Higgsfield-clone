import { sequenceCopy } from "./sequenceCopy"

type ExportGuidanceProps = {
  jobId: string | null
}

// Shown after render starts: where the film lands and what to do with it.
// Download / Share reuse the rail + /v/ paths; face swap is a copy pointer
// because the composer has no face-swap handoff in scope.
export function ExportGuidance({ jobId }: ExportGuidanceProps) {
  if (jobId === null) return null
  const guide = sequenceCopy.exportGuide
  return (
    <div aria-live="polite" className="flex flex-col gap-1 rounded-xl border border-border bg-sunken p-3">
      <p className="text-[13px] font-semibold text-text">{guide.heading}</p>
      <p className="text-[13px] text-muted">{guide.started}</p>
      <ul className="flex list-disc flex-col gap-1 pl-5 text-[13px] text-muted">
        <li>{guide.download}</li>
        <li>
          {guide.share}{" "}
          <a href={`/v/${jobId}`} className="underline hover:text-text">
            {`/v/${jobId}`}
          </a>
        </li>
        <li>{guide.faceswap}</li>
      </ul>
    </div>
  )
}
