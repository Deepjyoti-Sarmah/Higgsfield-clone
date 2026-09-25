import { Link } from "react-router-dom"
import { BrandMark } from "../../ui/BrandMark"
import { ButtonLink } from "../../ui/ButtonLink"
import type { PublicJob } from "../../api/share"
import { shareCopy } from "./shareCopy"

type ShareResultProps = {
  job: PublicJob
}

export function ShareResult({ job }: ShareResultProps) {
  const title = shareCopy.page.shareTitle(job)
  const meta = shareCopy.page.shareMeta(job)
  const videoUrl = job.kind === "image" ? null : job.video_url
  return (
    <div className="flex w-full flex-col items-center gap-4">
      <Link to="/" className="text-accent" aria-label="Reel & Still home">
        <BrandMark className="h-8 w-8" />
      </Link>
      {videoUrl !== null ? (
        <video
          src={videoUrl}
          poster={job.poster_url ?? undefined}
          controls
          playsInline
          preload="metadata"
          className="w-full max-w-2xl rounded-xl border border-border"
        />
      ) : (
        <div className="flex flex-wrap justify-center gap-3">
          {job.image_urls.map((url) => (
            <img
              key={url}
              src={url}
              alt=""
              className="max-h-[70dvh] rounded-xl border border-border object-contain"
            />
          ))}
        </div>
      )}
      <h1 className="text-center text-3xl text-text sm:text-4xl">{title}</h1>
      <p className="font-mono text-[13px] text-muted">{meta}</p>
      <ButtonLink to={shareCopy.page.ctaHref}>{shareCopy.page.cta}</ButtonLink>
    </div>
  )
}
