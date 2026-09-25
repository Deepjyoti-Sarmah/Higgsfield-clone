import { useState } from "react"
import type { ImageSettings, ImageSettingsControls } from "./imageCreateTypes"
import { DEFAULT_IMAGE_SETTINGS } from "./imageSettings"

export function useStillSettings(): ImageSettingsControls {
  const [settings, setSettings] = useState<ImageSettings>(DEFAULT_IMAGE_SETTINGS)
  return {
    settings,
    setAspectRatio: (value) => setSettings((current) => ({ ...current, aspectRatio: value })),
    setQuality: (value) => setSettings((current) => ({ ...current, quality: value })),
    setCount: (value) => setSettings((current) => ({ ...current, count: value })),
  }
}
