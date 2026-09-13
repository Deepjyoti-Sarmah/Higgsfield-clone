export function recreateHref(slug: string): string {
  return `/create/video?preset=${encodeURIComponent(slug)}`
}
