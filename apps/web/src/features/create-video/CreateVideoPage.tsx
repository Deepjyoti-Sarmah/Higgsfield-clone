import { useEffect, useRef, useState } from "react"
import type { RefObject } from "react"
import { useOutletContext } from "react-router-dom"
import { Toast } from "../../ui/Toast"
import type { SessionContextValue } from "../session/useSession"
import { CreateVideoCanvas } from "./CreateVideoCanvas"
import { CreateVideoPanel } from "./CreateVideoPanel"
import { deriveCanvasPhase } from "./canvasPhase"
import { createVideoCopy } from "./createVideoCopy"
import type { CanvasPhase, CanvasView, GenerateBlockedReason, ImageUploadControls, InsufficientCredits, JobWatch, Preset, PresetSelection, PresetsState, SubmitState, UploadState } from "./createVideoTypes"
import type { GenerateSectionProps } from "./GenerateSection"
import { SessionHistoryStrip } from "./SessionHistoryStrip"
import { StatusAnnouncer } from "./StatusAnnouncer"
import { useActiveJob } from "./useActiveJob"
import { useCredits } from "./useCredits"
import { useElapsedSeconds } from "./useElapsedSeconds"
import { useGuestSessionRunner } from "./useGuestSessionRunner"
import { useImageUpload } from "./useImageUpload"
import { usePrefersReducedMotion } from "./usePrefersReducedMotion"
import { usePresetSelection } from "./usePresetSelection"
import { usePresets } from "./usePresets"
import { useSessionHistory } from "./useSessionHistory"

const phaseMessages: Partial<Record<CanvasPhase, string>> = {
  uploading: createVideoCopy.announce.uploading, submitting: createVideoCopy.announce.starting,
  queued: createVideoCopy.announce.queued, generating: createVideoCopy.announce.generating,
  succeeded: createVideoCopy.announce.ready,
}

function announcementFor(phase: CanvasPhase, previous: CanvasPhase | null, isMissing: boolean, creditCost: number): string {
  if (phase === "ready") return previous === "uploading" ? createVideoCopy.announce.uploaded : ""
  if (phase !== "failed") return phaseMessages[phase] ?? ""
  return isMissing ? createVideoCopy.announce.missing : createVideoCopy.announce.failed(creditCost)
}

// The previous phase lives in a ref so the elapsed timer never re-announces.
function useStatusAnnouncement(phase: CanvasPhase, isMissing: boolean, creditCost: number): string {
  const [message, setMessage] = useState("")
  const previousPhaseRef = useRef<CanvasPhase | null>(null)
  useEffect(() => {
    const previous = previousPhaseRef.current
    previousPhaseRef.current = phase
    if (previous !== phase) setMessage(announcementFor(phase, previous, isMissing, creditCost))
  }, [phase, isMissing, creditCost])
  return message
}

function usePageTitle(): void {
  useEffect(() => {
    document.title = createVideoCopy.page.documentTitle
    return () => { document.title = createVideoCopy.page.appTitle }
  }, [])
}

// Focus follows the canvas heading on Generate; on mobile the canvas scrolls into view too.
function useCanvasFocus(focusSignal: string, headingRef: RefObject<HTMLHeadingElement | null>): void {
  const hasReducedMotion = usePrefersReducedMotion()
  const previousRef = useRef<string | null>(null)
  useEffect(() => {
    const previous = previousRef.current
    const heading = headingRef.current
    previousRef.current = focusSignal
    if (previous === null || previous === focusSignal || focusSignal === "" || !heading) return
    heading.focus()
    if (window.matchMedia("(max-width: 767px)").matches) {
      heading.scrollIntoView({ block: "start", behavior: hasReducedMotion ? "auto" : "smooth" })
    }
  }, [focusSignal, headingRef, hasReducedMotion])
}

function deriveBlockedReason(uploadStatus: UploadState["status"], hasPreset: boolean): GenerateBlockedReason | null {
  if (uploadStatus === "ready") return hasPreset ? null : "no-preset"
  if (uploadStatus === "uploading") return hasPreset ? "uploading" : "no-image-no-preset"
  return hasPreset ? "no-image" : "no-image-no-preset"
}
function deriveInsufficient(submitState: SubmitState, balance: number | null, preset: Preset | null): InsufficientCredits | null {
  if (submitState.status === "insufficient-credits") return submitState.insufficient
  if (balance === null || preset === null || balance >= preset.credit_cost) return null
  return { detail: "", balance, required: preset.credit_cost }
}
function buildCanvasView(presets: PresetsState, selection: PresetSelection, upload: ImageUploadControls, watch: JobWatch, elapsedSeconds: number): CanvasView {
  const thumbnail = upload.state.status === "idle" ? (watch.job?.input_image_url ?? null) : upload.state.previewUrl
  return {
    presetCount: presets.presets.length, hasPreset: selection.selectedPreset !== null,
    job: watch.job, isMissing: watch.isMissing, elapsedSeconds, wasRequeued: watch.wasRequeued,
    inputImageUrl: thumbnail, presetName: watch.job?.preset_name ?? selection.selectedPreset?.name ?? "",
  }
}
function useCreateVideoController() {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const presets = usePresets()
  const selection = usePresetSelection(presets)
  const upload = useImageUpload(run)
  const credits = useCredits(session.status === "signed-in")
  const history = useSessionHistory()
  const activeJob = useActiveJob({ run, history, credits, upload, selection })
  const [prompt, setPrompt] = useState("")
  const { watch } = activeJob
  const submitState = activeJob.createJob.state
  const elapsedSeconds = useElapsedSeconds(watch.job?.created_at ?? activeJob.submittedAtIso, watch.job?.finished_at ?? null)
  const phase = deriveCanvasPhase({ uploadStatus: upload.state.status, submitStatus: submitState.status, activeJobId: activeJob.activeJobId, jobStatus: watch.status, isJobMissing: watch.isMissing })
  return {
    presets, selection, upload, credits, history, activeJob, prompt, setPrompt, phase, submitState,
    canvas: buildCanvasView(presets, selection, upload, watch, elapsedSeconds),
    blockedReason: deriveBlockedReason(upload.state.status, selection.selectedPreset !== null),
    insufficient: deriveInsufficient(submitState, credits.balance, selection.selectedPreset),
    focusSignal: phase === "submitting" ? "submitting" : (activeJob.activeJobId ?? ""),
  }
}

type PageState = ReturnType<typeof useCreateVideoController>

// A new image, or a cheaper preset after a 402, makes the last submit result stale.
function useSubmitReset(page: PageState): void {
  const { upload, selection, submitState, activeJob } = page
  const previewKey = upload.state.status === "idle" ? "" : upload.state.previewUrl
  const previousRef = useRef({ previewKey, slug: selection.selectedSlug })
  const { resetSubmit } = activeJob.createJob
  useEffect(() => {
    const previous = previousRef.current
    previousRef.current = { previewKey, slug: selection.selectedSlug }
    const isNewPreset = previous.slug !== selection.selectedSlug
    if (previous.previewKey === previewKey && !(isNewPreset && submitState.status === "insufficient-credits")) return
    resetSubmit()
  }, [previewKey, selection.selectedSlug, submitState.status, resetSubmit])
}
function PageColumns({ page, headingRef }: { page: PageState; headingRef: RefObject<HTMLHeadingElement | null> }) {
  const { activeJob, history, canvas, phase, selection, upload, prompt, submitState } = page
  const generate: GenerateSectionProps = {
    selectedPreset: selection.selectedPreset,
    blockedReason: page.blockedReason,
    isSubmitting: submitState.status === "submitting",
    balance: page.credits.balanceView,
    insufficient: page.insufficient,
    submitError: submitState.status === "error" && submitState.errorKind !== "network" ? submitState.errorKind : null,
    onGenerate: () => {
      const preset = selection.selectedPreset
      if (preset === null || upload.state.status !== "ready") return
      activeJob.startJob({ presetSlug: preset.slug, presetName: preset.name, inputAssetId: upload.state.asset.id, prompt })
    },
  }
  return (
    <>
      <div className="md:sticky md:top-20 md:max-h-[calc(100dvh-7rem)] md:overflow-y-auto">
        <CreateVideoPanel upload={upload} presets={page.presets} selection={selection} prompt={prompt} onPromptChange={page.setPrompt} generate={generate} />
      </div>
      <div className="flex flex-col gap-6">
        <CreateVideoCanvas phase={phase} canvas={canvas} connection={activeJob.watch.connection} headingRef={headingRef} onMakeAnother={() => { activeJob.makeAnother(); focusPresetGroup() }} onRetry={activeJob.retryFailedJob} onDismissMissing={activeJob.dismissMissing} />
        <SessionHistoryStrip entries={history.entries} activeJobId={activeJob.activeJobId} onOpen={activeJob.openHistoryEntry} />
      </div>
    </>
  )
}

// The preset radios live inside the panel, so focus after "Make another" goes by name.
function focusPresetGroup(): void {
  document.querySelector<HTMLInputElement>('input[name="preset"]')?.focus()
}

type ToastKind = "submit" | "presets"

// Submit errors outrank preset errors; the toast stays until dismissed or replaced.
function usePageToast(page: PageState) {
  const { submitState, presets, activeJob } = page
  const isSubmitError = submitState.status === "error" && submitState.errorKind === "network"
  const kind: ToastKind | null = isSubmitError ? "submit" : presets.status === "error" ? "presets" : null
  const [dismissed, setDismissed] = useState<ToastKind | null>(null)
  const previousKindRef = useRef<ToastKind | null>(kind)
  useEffect(() => {
    if (previousKindRef.current === kind) return
    previousKindRef.current = kind
    setDismissed(null)
  }, [kind])
  if (kind === null || dismissed === kind) return null
  const onAction = () => {
    setDismissed(null)
    if (kind === "submit") activeJob.createJob.retrySubmit()
    else presets.reloadPresets()
  }
  const message = kind === "submit" ? createVideoCopy.generate.networkToast : createVideoCopy.preset.errorToast
  return { message, actionLabel: createVideoCopy.toast.retry, onAction, onDismiss: () => setDismissed(kind) }
}

export function CreateVideoPage() {
  const page = useCreateVideoController()
  const headingRef = useRef<HTMLHeadingElement>(null)
  usePageTitle()
  useCanvasFocus(page.focusSignal, headingRef)
  useSubmitReset(page)
  const announcement = useStatusAnnouncement(page.phase, page.canvas.isMissing, page.canvas.job?.credit_cost ?? 0)
  const toast = usePageToast(page)
  return (
    <div className="mx-auto grid w-full max-w-[1400px] gap-6 md:grid-cols-[360px_minmax(0,1fr)] md:items-start xl:grid-cols-[420px_minmax(0,1fr)]">
      <StatusAnnouncer message={announcement} />
      <PageColumns page={page} headingRef={headingRef} />
      {toast !== null && <Toast {...toast} />}
    </div>
  )
}
