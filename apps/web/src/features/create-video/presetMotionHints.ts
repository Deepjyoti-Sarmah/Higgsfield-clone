const zoomInClasses =
  "motion-safe:group-hover:animate-hf-motion-zoom-in " +
  "motion-safe:has-[:checked]:animate-hf-motion-zoom-in " +
  "motion-safe:has-[:focus-visible]:animate-hf-motion-zoom-in"

const zoomOutClasses =
  "motion-safe:group-hover:animate-hf-motion-zoom-out " +
  "motion-safe:has-[:checked]:animate-hf-motion-zoom-out " +
  "motion-safe:has-[:focus-visible]:animate-hf-motion-zoom-out"

const panLeftClasses =
  "motion-safe:group-hover:animate-hf-motion-pan-left " +
  "motion-safe:has-[:checked]:animate-hf-motion-pan-left " +
  "motion-safe:has-[:focus-visible]:animate-hf-motion-pan-left"

const panRightClasses =
  "motion-safe:group-hover:animate-hf-motion-pan-right " +
  "motion-safe:has-[:checked]:animate-hf-motion-pan-right " +
  "motion-safe:has-[:focus-visible]:animate-hf-motion-pan-right"

const tiltUpClasses =
  "motion-safe:group-hover:animate-hf-motion-tilt-up " +
  "motion-safe:has-[:checked]:animate-hf-motion-tilt-up " +
  "motion-safe:has-[:focus-visible]:animate-hf-motion-tilt-up"

const shakeClasses =
  "motion-safe:group-hover:animate-hf-motion-shake " +
  "motion-safe:has-[:checked]:animate-hf-motion-shake " +
  "motion-safe:has-[:focus-visible]:animate-hf-motion-shake"

const motionClassBySlug: Record<string, string> = {
  "dolly-in": zoomInClasses,
  "ken-burns": zoomInClasses,
  "orbit-push": zoomInClasses,
  "spiral-in": zoomInClasses,
  "crash-zoom": zoomInClasses,
  "dolly-out": zoomOutClasses,
  "pan-left": panLeftClasses,
  "whip-pan": panLeftClasses,
  "pan-right": panRightClasses,
  "slow-drift": panRightClasses,
  "tilt-up": tiltUpClasses,
  handheld: shakeClasses,
}

export function presetMotionClass(slug: string): string {
  return motionClassBySlug[slug] ?? zoomInClasses
}
