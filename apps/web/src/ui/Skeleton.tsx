type SkeletonProps = {
  className?: string
  label?: string
}

// A shimmer block matching the final layout's shape; shimmer is motion-safe.
export function Skeleton({ className = "h-4 w-full", label }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label={label ?? "Loading"}
      className={`relative overflow-hidden rounded-md bg-sunken ${className}`}
    >
      <div className="absolute inset-y-0 w-1/3 bg-surface motion-safe:animate-skeleton-shimmer" />
    </div>
  )
}
