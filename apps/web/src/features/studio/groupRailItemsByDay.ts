import type { LibraryItem } from "../../api/library"

export type RailDayGroup = {
  heading: string
  items: LibraryItem[]
}

function dayKey(iso: string): string {
  return iso.slice(0, 10)
}

function headingFor(day: string, today: string, yesterday: string): string {
  if (day === today) return "Today"
  if (day === yesterday) return "Yesterday"
  return day
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
