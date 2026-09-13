import { ButtonLink } from "../../ui/ButtonLink"
import { exploreCopy } from "./exploreCopy"

export function ExploreHero() {
  const { h1, subtitle, primaryCta, primaryHref, secondaryCta, secondaryHref } = exploreCopy.hero

  return (
    <section className="mx-auto flex max-w-3xl flex-col items-center gap-5 py-14 text-center sm:py-20">
      <h1 className="text-5xl leading-[1.02] sm:text-7xl">{h1}</h1>
      <p className="max-w-xl text-base text-muted">{subtitle}</p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <ButtonLink to={primaryHref}>{primaryCta}</ButtonLink>
        <ButtonLink to={secondaryHref} variant="secondary">
          {secondaryCta}
        </ButtonLink>
      </div>
    </section>
  )
}
