export const ACCEPTED_AUDIO_TYPES = ["audio/mpeg", "audio/mp4", "audio/wav"] as const
export const MAX_AUDIO_BYTES = 10 * 1024 * 1024

export type AudioFileError = "wrong-type" | "too-large" | "empty"

export function audioErrorKind(file: File): AudioFileError | null {
  if (!ACCEPTED_AUDIO_TYPES.includes(file.type as (typeof ACCEPTED_AUDIO_TYPES)[number])) {
    return "wrong-type"
  }
  if (file.size <= 0) return "empty"
  if (file.size > MAX_AUDIO_BYTES) return "too-large"
  return null
}
