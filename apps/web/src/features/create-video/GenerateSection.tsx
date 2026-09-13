import { Button } from "../../ui/Button"
import { ButtonLink } from "../../ui/ButtonLink"
import { createVideoCopy } from "./createVideoCopy"
import type {
  BalanceView,
  GenerateBlockedReason,
  InsufficientCredits,
  Preset,
  SubmitErrorKind,
} from "./createVideoTypes"

export type GenerateSectionProps = {
  selectedPreset: Preset | null
  blockedReason: GenerateBlockedReason | null
  isSubmitting: boolean
  balance: BalanceView
  insufficient: InsufficientCredits | null
  submitError: SubmitErrorKind | null
  onGenerate: () => void
}

type ActionProps = Pick<
  GenerateSectionProps,
  "selectedPreset" | "blockedReason" | "isSubmitting" | "insufficient" | "onGenerate"
>

const blockedMessage: Record<GenerateBlockedReason, string> = {
  "no-image-no-preset": createVideoCopy.generate.blockedNoImageNoPreset,
  "no-image": createVideoCopy.generate.blockedNoImage,
  "no-preset": createVideoCopy.generate.blockedNoPreset,
  uploading: createVideoCopy.generate.blockedUploading,
}

const submitErrorMessage: Record<SubmitErrorKind, string> = {
  network: createVideoCopy.generate.networkToast,
  "input-missing": createVideoCopy.generate.inputMissing,
  "input-not-ready": createVideoCopy.generate.inputNotReady,
  session: createVideoCopy.generate.sessionError,
  invalid: createVideoCopy.generate.invalid,
}

function balanceMessage(balance: BalanceView): string {
  if (balance.status === "known") return createVideoCopy.generate.balanceKnown(balance.balance)
  if (balance.status === "loading") return createVideoCopy.generate.balanceLoading
  if (balance.status === "error") return createVideoCopy.generate.balanceError
  return createVideoCopy.generate.guestOffer
}

function GenerateAction({
  selectedPreset,
  blockedReason,
  isSubmitting,
  insufficient,
  onGenerate,
}: ActionProps) {
  if (insufficient !== null) {
    return (
      <ButtonLink to="/credits" className="w-full">
        {createVideoCopy.generate.getCredits}
      </ButtonLink>
    )
  }
  const label = isSubmitting
    ? createVideoCopy.generate.submitting
    : selectedPreset === null
      ? createVideoCopy.generate.label
      : createVideoCopy.generate.withCost(selectedPreset.credit_cost)
  return (
    <Button
      className="w-full"
      isLoading={isSubmitting}
      disabled={blockedReason !== null}
      onClick={onGenerate}
    >
      {label}
    </Button>
  )
}

function BalanceLines({
  balance,
  insufficient,
}: Pick<GenerateSectionProps, "balance" | "insufficient">) {
  return (
    <>
      <p className="text-xs text-muted">{balanceMessage(balance)}</p>
      {insufficient !== null && (
        <p className="text-xs text-red-400">
          {createVideoCopy.generate.insufficient(insufficient.balance, insufficient.required)}
        </p>
      )}
    </>
  )
}

function SubmitErrorLine({ kind }: { kind: SubmitErrorKind }) {
  return (
    <p role="alert" className="text-xs text-red-400">
      {submitErrorMessage[kind]}
    </p>
  )
}

export function GenerateSection(props: GenerateSectionProps) {
  const { blockedReason, balance, insufficient, submitError } = props
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">
        {createVideoCopy.generate.label}
      </p>
      {blockedReason !== null && (
        <p className="text-xs text-muted">{blockedMessage[blockedReason]}</p>
      )}
      <GenerateAction {...props} />
      <BalanceLines balance={balance} insufficient={insufficient} />
      {submitError !== null && <SubmitErrorLine kind={submitError} />}
    </div>
  )
}
