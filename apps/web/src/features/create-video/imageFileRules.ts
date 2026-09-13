export const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"] as const
export const MAX_IMAGE_BYTES = 10_485_760

export function checkImageFile(file: File): boolean {
  const isAcceptedType = ACCEPTED_IMAGE_TYPES.some((type) => type === file.type)
  return isAcceptedType && file.size > 0 && file.size <= MAX_IMAGE_BYTES
}
