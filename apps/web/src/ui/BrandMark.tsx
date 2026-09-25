type BrandMarkProps = {
  className?: string
}

// A small frame with sprocket notches and a record-light dot, in currentColor.
export function BrandMark({ className = "h-6 w-6" }: BrandMarkProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="2.75" y="5.25" width="18.5" height="13.5" rx="2.75" stroke="currentColor" strokeWidth="1.5" />
      <rect x="2.75" y="9" width="18.5" height="1" fill="currentColor" opacity="0.35" />
      <rect x="2.75" y="14" width="18.5" height="1" fill="currentColor" opacity="0.35" />
      <circle cx="12" cy="12" r="2" fill="currentColor" />
    </svg>
  )
}

export function BrandWordmark() {
  return (
    <span className="font-display text-xl leading-none text-text">
      Reel &amp; Still
    </span>
  )
}
