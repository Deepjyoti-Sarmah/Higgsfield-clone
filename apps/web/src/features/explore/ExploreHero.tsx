import { ButtonLink } from "../../ui/ButtonLink"
import { exploreCopy } from "./exploreCopy"

export function ExploreHero() {
  const { h1, subtitle, primaryCta, primaryHref, secondaryCta, secondaryHref } = exploreCopy.hero

  return (
    <section className="mx-auto flex w-full max-w-4xl flex-col items-center gap-3 py-4 text-center">
      <span className="rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-widest text-accent">
        ✦ Next-Gen AI Video & Image Creation
      </span>
      <h1 className="text-3xl leading-[1.02] tracking-tight sm:text-5xl">{h1}</h1>
      <p className="max-w-xl text-sm text-muted">{subtitle}</p>
      <div className="mt-1 flex flex-wrap items-center justify-center gap-3">
        <ButtonLink to={primaryHref}>{primaryCta}</ButtonLink>
        <ButtonLink to={secondaryHref} variant="secondary">
          {secondaryCta}
        </ButtonLink>
      </div>
    </section>
  )
}
