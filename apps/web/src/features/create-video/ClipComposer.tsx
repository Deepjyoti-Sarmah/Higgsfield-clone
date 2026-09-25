import { useCallback, useState } from "react"
import { useOutletContext } from "react-router-dom"
import { useGuestSessionRunner } from "../../api/guestSession"
import { usePresets } from "../../api/presets"
import { useCreditsPopover } from "../../ui/useCreditsPopover"
import type { ComposerProps, SeedImage } from "../../api/studioContracts"
import type { SessionContextValue } from "../session/useSession"
import { clipBlockedMessage } from "./clipSubmit"
import { ClipActions } from "./ClipActions"
import { createVideoCopy } from "./createVideoCopy"
import { ImageDropZone } from "./ImageDropZone"
import { PresetPicker } from "./PresetPicker"
import { PromptField } from "./PromptField"
import { SeededStill } from "./SeededStill"
import { useClipInput } from "./useClipInput"
import { useClipSubmit } from "./useClipSubmit"
import { useImageUpload } from "./useImageUpload"
import { usePresetSelection } from "./usePresetSelection"
import { useSeedAdoption } from "./useSeedAdoption"

type ClipComposerProps = ComposerProps & {
  seedImage: SeedImage | null
  onSeedConsumed: () => void
}

function ClipInputSection(props: {
  fromSeed: boolean
  previewUrl: string | null
  upload: ReturnType<typeof useImageUpload>
  onSeedDropped: () => void
}) {
  if (props.fromSeed) {
    return <SeededStill previewUrl={props.previewUrl} onReplace={props.onSeedDropped} />
  }
  return <ImageDropZone upload={props.upload} />
}

export function ClipComposer({ onJobStarted, seedImage, onSeedConsumed }: ClipComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const presets = usePresets()
  const selection = usePresetSelection(presets)
  const upload = useImageUpload(run)
  const { openCredits } = useCreditsPopover()
  const submitState = useClipSubmit(run, onJobStarted, openCredits)
  const [prompt, setPrompt] = useState("")
  const clipInput = useClipInput(seedImage, upload, selection)
  const preset = selection.selectedPreset
  useSeedAdoption(clipInput.input?.fromSeed === true ? seedImage : null, onSeedConsumed)

  const handleSubmit = useCallback(() => {
    if (clipInput.input === null || preset === null) return
    submitState.submit(clipInput.input, preset.slug, prompt)
  }, [clipInput.input, preset, prompt, submitState])

  return (
    <div className="flex flex-col gap-4 px-4 py-5 sm:px-6">
      <ClipInputSection
        fromSeed={clipInput.input?.fromSeed === true}
        previewUrl={clipInput.previewUrl}
        upload={upload}
        onSeedDropped={clipInput.dropSeed}
      />
      <PresetPicker presets={presets} selection={selection} previewImageUrl={clipInput.previewUrl} />
      <PromptField value={prompt} onChange={setPrompt} />
      <ClipActions
        cost={preset?.credit_cost ?? null}
        isBlocked={clipInput.blocked !== null}
        isSubmitting={submitState.isSubmitting}
        blockedMessage={clipBlockedMessage(clipInput.blocked, createVideoCopy.generate)}
        insufficient={submitState.insufficient}
        failure={submitState.failure}
        onSubmit={handleSubmit}
      />
    </div>
  )
}
