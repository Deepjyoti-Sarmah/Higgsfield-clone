import { useCallback, useEffect, useState } from "react"
import { useOutletContext } from "react-router-dom"
import { useGuestSessionRunner } from "../../api/guestSession"
import { Tabs } from "../../ui/Tabs"
import { useCreditsPopover } from "../../ui/useCreditsPopover"
import type { FaceSwapComposerProps } from "../../api/studioContracts"
import type { SessionContextValue } from "../session/useSession"
import { FACESWAP_CREDIT_COST } from "./faceSwapCost"
import { faceSwapCopy } from "./faceSwapCopy"
import { FaceSwapActions } from "./FaceSwapActions"
import { FaceSwapWells } from "./FaceSwapWells"
import { ImageWell } from "./ImageWell"
import { useFaceSwapSubmit } from "./useFaceSwapSubmit"
import { useFaceSwapWells } from "./useFaceSwapWells"
import { VideoFaceSwapPreview } from "./VideoFaceSwapPreview"
import { VideoFaceSwapRender } from "./VideoFaceSwapRender"
import { VideoTargetWell } from "./VideoTargetWell"
import { useVideoTargetWell } from "./useVideoTargetWell"
import { isVideoSeedUrl } from "./videoFaceSwapCost"

type TargetMode = "image" | "video"

const TARGET_TABS = [
  { value: "image", label: "Photo target" },
  { value: "video", label: "Video target" },
] as const

function GuidanceBlock() {
  return (
    <section
      aria-label={faceSwapCopy.guidance.title}
      className="rounded-xl border border-border bg-sunken p-3"
    >
      <p className="text-sm font-medium text-text">{faceSwapCopy.guidance.title}</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-5 text-[13px] text-muted">
        {faceSwapCopy.guidance.points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
    </section>
  )
}

function pickVideoSeed(seedTarget: FaceSwapComposerProps["seedTarget"]) {
  if (seedTarget === null) return null
  return isVideoSeedUrl(seedTarget.url) ? seedTarget : null
}

function useTargetMode(seedTarget: FaceSwapComposerProps["seedTarget"]) {
  const [mode, setMode] = useState<TargetMode>("image")
  const videoSeed = pickVideoSeed(seedTarget)
  const imageSeed = videoSeed !== null ? null : seedTarget
  if (videoSeed !== null && mode === "image") setMode("video")
  if (videoSeed === null && imageSeed !== null && mode === "video") setMode("image")
  return { mode, setMode, videoSeed, imageSeed }
}

function ImageSwapSection({ composer }: { composer: ReturnType<typeof useImageSwap> }) {
  return (
    <>
      <FaceSwapWells faceUpload={composer.wells.faceUpload} targetUpload={composer.wells.targetUpload} heldTarget={composer.wells.heldTarget} />
      <FaceSwapActions
        cost={FACESWAP_CREDIT_COST}
        blocked={composer.wells.blocked}
        isSubmitting={composer.submitState.isSubmitting}
        insufficient={composer.submitState.insufficient}
        failure={composer.submitState.failure}
        onSubmit={composer.handleSubmit}
      />
    </>
  )
}

function useImageSwap(
  run: ReturnType<typeof useGuestSessionRunner>,
  onJobStarted: (jobId: string) => void,
  openCredits: () => void,
  imageSeed: FaceSwapComposerProps["seedTarget"],
  onSeedConsumed: () => void,
) {
  const wells = useFaceSwapWells(run, imageSeed, onSeedConsumed)
  const submitState = useFaceSwapSubmit(run, onJobStarted, openCredits)
  const { face, target } = wells
  const handleSubmit = useCallback(() => {
    if (face === null || target === null) return
    submitState.submit(face.assetId, target.assetId)
  }, [face, target, submitState])
  return { wells, submitState, handleSubmit }
}

function VideoSwapSection({ composer }: { composer: ReturnType<typeof useVideoSwap> }) {
  return (
    <>
      <ImageWell
        label={faceSwapCopy.face.label}
        hint={faceSwapCopy.face.hint}
        seedUrl={null}
        onDropSeed={() => undefined}
        upload={composer.wells.faceUpload}
      />
      <VideoTargetWell target={composer.video} />
      <VideoFaceSwapPreview
        key={composer.video.url ?? "none"}
        run={composer.run}
        faceAssetId={composer.wells.face?.assetId ?? null}
        targetUrl={composer.video.url}
        onKeyframeReady={composer.setKeyframeAssetId}
      />
      <VideoFaceSwapRender
        run={composer.run}
        faceAssetId={composer.wells.face?.assetId ?? null}
        targetReady={composer.video.url !== null}
        targetAssetId={composer.video.targetAssetId}
        durationMs={composer.video.durationMs}
        keyframeAssetId={composer.keyframeAssetId}
        onJobStarted={composer.onJobStarted}
        onInsufficient={composer.openCredits}
      />
    </>
  )
}

function useVideoSwap(
  run: ReturnType<typeof useGuestSessionRunner>,
  onJobStarted: (jobId: string) => void,
  openCredits: () => void,
  videoSeed: FaceSwapComposerProps["seedTarget"],
  onSeedConsumed: () => void,
  wells: ReturnType<typeof useFaceSwapWells>,
) {
  const video = useVideoTargetWell(videoSeed, onSeedConsumed)
  const [keyframeAssetId, setKeyframeAssetId] = useState<string | null>(null)
  const targetKey = video.url ?? "none"
  useEffect(() => {
    setKeyframeAssetId(null)
  }, [targetKey])
  return { run, onJobStarted, openCredits, wells, video, keyframeAssetId, setKeyframeAssetId }
}

export function FaceSwapComposer({ onJobStarted, seedTarget, onSeedConsumed }: FaceSwapComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const { openCredits } = useCreditsPopover()
  const target = useTargetMode(seedTarget)

  const image = useImageSwap(run, onJobStarted, openCredits, target.imageSeed, onSeedConsumed)
  const video = useVideoSwap(run, onJobStarted, openCredits, target.videoSeed, onSeedConsumed, image.wells)

  return (
    <div className="flex flex-col gap-4 px-4 py-5 sm:px-6">
      <GuidanceBlock />
      <Tabs items={TARGET_TABS} value={target.mode} onChange={target.setMode} ariaLabel="Face swap target type" />
      {target.mode === "image" ? <ImageSwapSection composer={image} /> : <VideoSwapSection composer={video} />}
    </div>
  )
}
