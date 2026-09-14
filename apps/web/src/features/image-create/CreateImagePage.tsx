import { useEffect, useRef, useState } from "react"
import { useOutletContext } from "react-router-dom"
import { useCreditBalance } from "../../api/credits"
import { useImageJob } from "../../api/imageJobs"
import type { ImageJobControls } from "../../api/imageJobs"
import { useImageOptions } from "../../api/imageOptions"
import type { ImageOptions } from "../../api/imageOptions"
import { useElapsedSeconds } from "../../api/useElapsedSeconds"
import type { SessionContextValue } from "../session/useSession"
import { ImageComposer } from "./ImageComposer"
import { ImageStage } from "./ImageStage"
import type { ImageStageProgress } from "./ImageStage"
import { imageCreateCopy } from "./imageCreateCopy"
import type {
  ImageBalance,
  ImageGenerateProps,
  ImageSettings,
  ImageSettingsControls,
} from "./imageCreateTypes"
import { DEFAULT_IMAGE_SETTINGS, blockedReason, deriveImagePhase, imageCost } from "./imageSettings"
import { useImageJobProgress } from "./useImageJobProgress"

function useSettingsControls(): ImageSettingsControls {
  const [settings, setSettings] = useState<ImageSettings>(DEFAULT_IMAGE_SETTINGS)
  return {
    settings,
    setAspectRatio: (value) => setSettings((current) => ({ ...current, aspectRatio: value })),
    setQuality: (value) => setSettings((current) => ({ ...current, quality: value })),
    setCount: (value) => setSettings((current) => ({ ...current, count: value })),
  }
}

function buildGenerateProps(input: {
  prompt: string
  options: ImageOptions | null
  settings: ImageSettings
  balance: ImageBalance
  job: ImageJobControls
}): ImageGenerateProps {
  const blocked = blockedReason(input.prompt, input.options)
  const isSubmitting = input.job.phase === "submitting"
  return {
    cost: input.options === null ? 0 : imageCost(input.options, input.settings),
    canGenerate: blocked === null && !isSubmitting,
    blockedReason: blocked,
    isSubmitting,
    balance: input.balance,
    insufficient: input.job.insufficient,
    submitError: input.job.submitError,
    onGenerate: () =>
      input.job.submit({
        prompt: input.prompt,
        aspect_ratio: input.settings.aspectRatio,
        quality: input.settings.quality,
        count: input.settings.count,
      }),
  }
}

function useSubmittedAtIso(jobPhase: ImageJobControls["phase"]): string | null {
  const [submittedAtIso, setSubmittedAtIso] = useState<string | null>(null)
  const wasIdleRef = useRef(true)
  useEffect(() => {
    if (jobPhase === "idle") {
      wasIdleRef.current = true
      setSubmittedAtIso(null)
      return
    }
    if (jobPhase === "submitting" && wasIdleRef.current) {
      wasIdleRef.current = false
      setSubmittedAtIso(new Date().toISOString())
    }
  }, [jobPhase])
  return submittedAtIso
}

function useImageProgress(job: ImageJobControls): ImageStageProgress {
  const submittedAtIso = useSubmittedAtIso(job.phase)
  const progressWatch = useImageJobProgress(job.job?.id ?? null)
  const elapsedSeconds = useElapsedSeconds(submittedAtIso, job.job?.finished_at ?? null)
  return {
    elapsedSeconds,
    wasRequeued: progressWatch.wasRequeued,
    connection: progressWatch.connection,
  }
}

function useComposerState(session: SessionContextValue) {
  const optionsState = useImageOptions()
  const balance = useCreditBalance(session)
  const job = useImageJob(session)
  const [prompt, setPrompt] = useState("")
  const settings = useSettingsControls()
  const generate = buildGenerateProps({
    prompt,
    options: optionsState.options,
    settings: settings.settings,
    balance: { status: balance.status, balance: balance.balance },
    job,
  })
  return { optionsState, job, prompt, setPrompt, settings, generate }
}

export function CreateImagePage() {
  const session = useOutletContext<SessionContextValue>()
  const { optionsState, job, prompt, setPrompt, settings, generate } = useComposerState(session)
  const phase = deriveImagePhase({ optionsStatus: optionsState.status, jobPhase: job.phase })
  const progress = useImageProgress(job)

  return (
    <section className="mx-auto flex w-full max-w-3xl flex-col gap-8 py-4">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-text">{imageCreateCopy.page.title}</h1>
        <p className="text-muted">{imageCreateCopy.page.subtitle}</p>
      </header>
      <ImageComposer
        options={optionsState}
        settings={settings}
        prompt={prompt}
        onPromptChange={setPrompt}
        generate={generate}
      />
      <ImageStage
        phase={phase}
        watch={{ job: job.job }}
        prompt={prompt}
        progress={progress}
        onRetry={job.retryRead}
        onMakeAnother={job.resetSubmit}
      />
    </section>
  )
}
