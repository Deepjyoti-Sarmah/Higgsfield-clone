const createdAtFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
})

const createdAtTimeFormat = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
})

// CLDR 42+ abbreviates September as "Sept" in en-GB; the design fixes the "Sep" text.
function normalizeShortMonth(part: Intl.DateTimeFormatPart): string {
  return part.type === "month" && part.value === "Sept" ? "Sep" : part.value
}

// The rail groups items by day, so the per-row stamp only needs the time.
export function formatCreatedTime(iso: string): string {
  if (!iso) return ""
  const timestamp = Date.parse(iso)
  if (Number.isNaN(timestamp)) return ""
  return createdAtTimeFormat.format(timestamp)
}

export function formatCreatedAt(iso: string): string {
  if (!iso) return ""
  const timestamp = Date.parse(iso)
  if (Number.isNaN(timestamp)) return ""
  return createdAtFormat
    .formatToParts(timestamp)
    .map(normalizeShortMonth)
    .join("")
}
