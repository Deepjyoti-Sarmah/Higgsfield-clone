// Pure helper so the arrow-key wrap can be unit-tested without a DOM.
export function nextTabIndex(count: number, current: number, key: string): number {
  if (key === "ArrowRight") return (current + 1) % count
  if (key === "ArrowLeft") return (current - 1 + count) % count
  if (key === "Home") return 0
  if (key === "End") return count - 1
  return current
}
