import { useEffect } from "react"
import { ACCEPTED_IMAGE_TYPES } from "./imageFileRules"

function isAcceptedImage(file: File): boolean {
  return (ACCEPTED_IMAGE_TYPES as readonly string[]).includes(file.type)
}

function findPastedImage(files: FileList | null): File | null {
  if (!files) return null
  const images = Array.from(files).filter(isAcceptedImage)
  return images.length > 0 ? images[0] : null
}

// Only image pastes are claimed, so text pasted into the prompt still lands there.
export function useClipboardImagePaste(onImage: (file: File) => void): void {
  useEffect(() => {
    function handlePaste(event: ClipboardEvent) {
      const image = findPastedImage(event.clipboardData?.files ?? null)
      if (!image) return
      event.preventDefault()
      onImage(image)
    }
    window.addEventListener("paste", handlePaste)
    return () => window.removeEventListener("paste", handlePaste)
  }, [onImage])
}
