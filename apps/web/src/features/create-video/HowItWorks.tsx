import { createVideoCopy } from "./createVideoCopy"
import type { HowItWorksStepState, StepIllustration } from "./HowItWorksStep"
import { HowItWorksStep } from "./HowItWorksStep"

type HowItWorksPhase = "empty" | "uploading" | "ready"

type HowItWorksProps = {
  phase: HowItWorksPhase
  hasPreset: boolean
  presetCount: number
}

type StepDefinition = {
  title: string
  body: string
  illustration: StepIllustration
}

const stepStatesByPhase: Record<
  Exclude<HowItWorksPhase, "ready">,
  [HowItWorksStepState, HowItWorksStepState, HowItWorksStepState]
> = {
  empty: ["current", "todo", "todo"],
  uploading: ["busy", "current", "todo"],
}

function stepStates(
  phase: HowItWorksPhase,
  hasPreset: boolean,
): [HowItWorksStepState, HowItWorksStepState, HowItWorksStepState] {
  if (phase !== "ready") return stepStatesByPhase[phase]
  return hasPreset ? ["done", "done", "current"] : ["done", "current", "todo"]
}

function stepDefinitions(presetCount: number): StepDefinition[] {
  return [
    {
      title: createVideoCopy.howItWorks.step1Title,
      body: createVideoCopy.howItWorks.step1Body,
      illustration: "image",
    },
    {
      title: createVideoCopy.howItWorks.step2Title,
      body: createVideoCopy.howItWorks.step2Body(presetCount),
      illustration: "preset",
    },
    {
      title: createVideoCopy.howItWorks.step3Title,
      body: createVideoCopy.howItWorks.step3Body,
      illustration: "video",
    },
  ]
}

export function HowItWorks({ phase, hasPreset, presetCount }: HowItWorksProps) {
  const states = stepStates(phase, hasPreset)
  const steps = stepDefinitions(presetCount)
  return (
    <div className="flex w-full flex-col items-center gap-6">
      <p className="max-w-xl text-center text-sm text-muted">{createVideoCopy.howItWorks.sub}</p>
      <ol className="grid w-full gap-3 sm:grid-cols-3">
        {steps.map((step, position) => (
          <HowItWorksStep
            key={step.title}
            index={(position + 1) as 1 | 2 | 3}
            title={step.title}
            body={step.body}
            state={states[position] ?? "todo"}
            illustration={step.illustration}
          />
        ))}
      </ol>
    </div>
  )
}
