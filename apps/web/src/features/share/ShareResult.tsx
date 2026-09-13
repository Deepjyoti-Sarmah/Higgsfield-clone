import type { PublicJob } from "../../api/share"
import { buttonClasses } from "../../ui/buttonStyles"
import { ButtonLink } from "../../ui/ButtonLink"
import { shareCopy } from "./shareCopy"

type ShareResultProps = {
  job: PublicJob
}

export function ShareResult({ job }: ShareResultProps) {
  const videoUrl = job.video_url
  return (
    <div className="flex w-full flex-col items-center gap-4">
      <h1 className="text-center text-3xl text-text sm:text-4xl">{job.preset_name}</h1>
      {videoUrl === null ? null : (
        <video
          src={videoUrl}
          poster={job.poster_url ?? undefined}
          controls
          muted
          playsInline
          loop
          preload="metadata"
          className="w-full max-w-2xl rounded-xl border border-border"
        />
      )}
      <p className="text-xs text-muted">{shareCopy.page.attribution}</p>
      {videoUrl === null ? null : (
        <a href={videoUrl} download className={buttonClasses("secondary")}>
          {shareCopy.result.download}
        </a>
      )}
      <ButtonLink to={shareCopy.page.ctaHref}>{shareCopy.page.cta}</ButtonLink>
    </div>
  )
}
