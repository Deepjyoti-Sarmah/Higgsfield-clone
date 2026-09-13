import { useEffect, useRef } from "react"
import type { RefObject } from "react"
import { createVideoCopy } from "./createVideoCopy"
import type {
  ImageUploadControls,
  PresetSelection,
  PresetsState,
} from "./createVideoTypes"
import type { GenerateSectionProps } from "./GenerateSection"
import { GenerateSection } from "./GenerateSection"
import { ImageDropZone } from "./ImageDropZone"
import { PresetPicker } from "./PresetPicker"
import { PromptField } from "./PromptField"

type CreateVideoPanelProps = {
  upload: ImageUploadControls
  presets: PresetsState
  selection: PresetSelection
  prompt: string
  onPromptChange: (value: string) => void
  generate: GenerateSectionProps
}

function SectionLabel({ text }: { text: string }) {
  return <p className="text-xs font-semibold uppercase tracking-wide text-muted">{text}</p>
}

function pickRadioToFocus(groupRef: RefObject<HTMLFieldSetElement | null>): HTMLElement | null {
  const group = groupRef.current
  if (!group) return null
  const checked = group.querySelector<HTMLInputElement>("input:checked")
  if (checked) return checked
  return group.querySelector<HTMLInputElement>('input[type="radio"]')
}

// The visitor's focus only moves off the zone if they were still in it, as the design requires.
function useFocusPresetAfterUpload(
  status: ImageUploadControls["state"]["status"],
  groupRef: RefObject<HTMLFieldSetElement | null>,
) {
  const previousStatusRef = useRef(status)
  useEffect(() => {
    const previous = previousStatusRef.current
    previousStatusRef.current = status
    if (previous !== "uploading" || status !== "ready") return
    if (!groupRef.current?.contains(document.activeElement)) return
    pickRadioToFocus(groupRef)?.focus()
  }, [status, groupRef])
}

export function CreateVideoPanel({
  upload,
  presets,
  selection,
  prompt,
  onPromptChange,
  generate,
}: CreateVideoPanelProps) {
  const groupRef = useRef<HTMLFieldSetElement>(null)
  useFocusPresetAfterUpload(upload.state.status, groupRef)
  const previewImageUrl = upload.state.status === "idle" ? null : upload.state.previewUrl

  return (
    <div className="rounded-2xl border border-border bg-surface">
      <div className="p-4">
        <h1 className="text-xl">{createVideoCopy.page.title}</h1>
      </div>
      <div className="border-t border-border p-4">
        <SectionLabel text={createVideoCopy.page.imageSection} />
        <div className="mt-3">
          <ImageDropZone upload={upload} />
        </div>
      </div>
      <div className="border-t border-border p-4">
        <PresetPicker
          presets={presets}
          selection={selection}
          previewImageUrl={previewImageUrl}
          groupRef={groupRef}
        />
      </div>
      <div className="border-t border-border p-4">
        <PromptField value={prompt} onChange={onPromptChange} />
      </div>
      <div className="sticky bottom-0 border-t border-border bg-surface p-4">
        <GenerateSection {...generate} />
      </div>
    </div>
  )
}
