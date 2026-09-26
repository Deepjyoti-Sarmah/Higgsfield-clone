// Jobs hold and settle credits server-side; the top-bar balance lives elsewhere, so a job
// start or finish announces it and every balance hook reloads.
const CREDITS_CHANGED_EVENT = "reel-and-still:credits-changed"

export function announceCreditsChanged(): void {
  window.dispatchEvent(new Event(CREDITS_CHANGED_EVENT))
}

export function listenForCreditsChanged(onChanged: () => void): () => void {
  window.addEventListener(CREDITS_CHANGED_EVENT, onChanged)
  return () => window.removeEventListener(CREDITS_CHANGED_EVENT, onChanged)
}
