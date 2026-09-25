// Pure helper so Escape handling can be unit-tested without a DOM.
export function isDismissKey(key: string): boolean {
  return key === "Escape"
}
