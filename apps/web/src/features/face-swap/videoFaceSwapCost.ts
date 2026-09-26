// Mirrors app.domain.video_faceswap_rules: per-second render cost and target limits.
// The create response returns the actual cost, so this is only the pre-submit label.
export const VIDEO_FACESWAP_CREDITS_PER_SECOND = 2
export const VIDEO_FACESWAP_MAX_SECONDS = 30
export const VIDEO_FACESWAP_MAX_BYTES = 50_000_000
export const VIDEO_FACESWAP_TARGET_MIME = "video/mp4"

export function videoRenderCost(durationMs: number | null | undefined): number | null {
  if (durationMs === null || durationMs === undefined || durationMs <= 0) return null
  return Math.ceil(durationMs / 1000) * VIDEO_FACESWAP_CREDITS_PER_SECOND
}

export type VideoFileRejection = "invalid-type" | "too-big"

export function checkVideoFile(file: File): VideoFileRejection | null {
  const isMp4 = file.type === VIDEO_FACESWAP_TARGET_MIME || file.name.toLowerCase().endsWith(".mp4")
  if (!isMp4) return "invalid-type"
  if (file.size <= 0 || file.size > VIDEO_FACESWAP_MAX_BYTES) return "too-big"
  return null
}

export function isVideoTargetTooLong(durationMs: number | null): boolean {
  return durationMs !== null && durationMs > VIDEO_FACESWAP_MAX_SECONDS * 1000
}

// Stage seeds carry no kind flag, so route rail seeds by URL: rail clips are mp4,
// rail stills are png/jpg. Only used to pick the image vs video well.
export function isVideoSeedUrl(url: string): boolean {
  return /\.(mp4|mov|webm)(\?|#|$)/i.test(url)
}
