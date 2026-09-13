import { Link } from "react-router-dom"
import { previewClipUrl, SHOWCASE_MEDIA } from "../../api/webMedia"
import { ButtonLink } from "../../ui/ButtonLink"
import { exploreCopy } from "./exploreCopy"

const HERO_SHOWCASE_CARDS = [
  {
    ...SHOWCASE_MEDIA.dollyIn,
    videoUrl: previewClipUrl(SHOWCASE_MEDIA.dollyIn.slug),
    to: "/create/video",
  },
  {
    ...SHOWCASE_MEDIA.orbitPush,
    videoUrl: previewClipUrl(SHOWCASE_MEDIA.orbitPush.slug),
    to: "/create/video?preset=orbit-push",
  },
  {
    ...SHOWCASE_MEDIA.crashZoom,
    videoUrl: previewClipUrl(SHOWCASE_MEDIA.crashZoom.slug),
    to: "/create/video?preset=crash-zoom",
  },
]

type ShowcaseCard = (typeof HERO_SHOWCASE_CARDS)[number]

function HeroShowcaseCard({ card }: { card: ShowcaseCard }) {
  return (
    <Link
      to={card.to}
      className="group relative aspect-[16/10] overflow-hidden rounded-2xl border border-border bg-surface shadow-xl transition-all duration-300 hover:border-accent/80 hover:shadow-accent/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <video
        src={card.videoUrl}
        autoPlay
        loop
        muted
        playsInline
        className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
      />
      <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-bg/90 via-bg/30 to-transparent p-4 text-left">
        <span className="text-[10px] font-bold uppercase tracking-widest text-accent">
          {card.tag}
        </span>
        <h2 className="font-display text-lg text-text">{card.title}</h2>
      </div>
    </Link>
  )
}

export function ExploreHero() {
  const { h1, subtitle, primaryCta, primaryHref, secondaryCta, secondaryHref } = exploreCopy.hero

  return (
    <section className="mx-auto flex max-w-6xl flex-col items-center gap-8 py-10 text-center sm:py-16">
      <div className="flex max-w-3xl flex-col items-center gap-4">
        <span className="rounded-full border border-accent/40 bg-accent/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-widest text-accent">
          ✦ Next-Gen AI Video & Image Creation
        </span>
        <h1 className="text-5xl leading-[1.02] tracking-tight sm:text-7xl">{h1}</h1>
        <p className="max-w-xl text-base text-muted">{subtitle}</p>
        <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
          <ButtonLink to={primaryHref}>{primaryCta}</ButtonLink>
          <ButtonLink to={secondaryHref} variant="secondary">
            {secondaryCta}
          </ButtonLink>
        </div>
      </div>

      <div className="mt-4 grid w-full grid-cols-1 gap-4 sm:grid-cols-3">
        {HERO_SHOWCASE_CARDS.map((card) => (
          <HeroShowcaseCard key={card.title} card={card} />
        ))}
      </div>
    </section>
  )
}
