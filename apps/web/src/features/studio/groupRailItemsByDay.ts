import type { LibraryItem } from "../../api/library"

export type RailDayGroup = {
  heading: string
  items: LibraryItem[]
}

function dayKey(iso: string): string {
  return iso.slice(0, 10)
}

const dayFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric", month: "short", timeZone: "UTC",
})
const dayYearFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
})

// Older groups read "14 Sep" (or "14 Sep 2025" outside the current year), not a raw ISO date.
// Keep the DESIGN "Sep" spelling (en-GB CLDR renders September as "Sept").
function headingForDay(day: string, today: string): string {
  const date = new Date(`${day}T00:00:00Z`)
  if (Number.isNaN(date.getTime())) return day
  const format = day.slice(0, 4) === today.slice(0, 4) ? dayFormat : dayYearFormat
  return format
    .formatToParts(date)
    .map((part) => (part.type === "month" && part.value === "Sept" ? "Sep" : part.value))
    .join("")
}

function headingFor(day: string, today: string, yesterday: string): string {
  if (day === today) return "Today"
  if (day === yesterday) return "Yesterday"
  return headingForDay(day, today)
}

// Groups newest first into Today / Yesterday / date headings.
export function groupRailItemsByDay(items: LibraryItem[], now: Date = new Date()): RailDayGroup[] {
  const formatter = (date: Date) => date.toISOString().slice(0, 10)
  const today = formatter(now)
  const yesterday = formatter(new Date(now.getTime() - 86_400_000))
  const groups: RailDayGroup[] = []
  const byDay = new Map<string, LibraryItem[]>()
  for (const item of items) {
    const day = dayKey(item.created_at)
    const bucket = byDay.get(day)
    if (bucket) bucket.push(item)
    else byDay.set(day, [item])
  }
  for (const [day, dayItems] of byDay) {
    groups.push({ heading: headingFor(day, today, yesterday), items: dayItems })
  }
  return groups
}
