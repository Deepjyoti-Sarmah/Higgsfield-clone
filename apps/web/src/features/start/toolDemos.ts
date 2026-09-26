import type { ShowcaseMedia } from "../../api/webMedia"
import { findShowcaseItem } from "../../api/webMedia"
import type { StepTool } from "./startCopy"

export type ToolDemo = {
  media: ShowcaseMedia
  alt: string
}

// The four tool demos. Still and Clip pull from different source stills on purpose.
export const TOOL_DEMOS: Record<StepTool, ToolDemo> = {
  still: { media: findShowcaseItem("neon-alley"), alt: "A still made from a text prompt" },
  clip: {
    media: findShowcaseItem("spiral-in"),
    alt: "A still animated with the Spiral In motion preset",
  },
  sequence: { media: findShowcaseItem("sequence-example"), alt: "Two clips cut into one sequence" },
  faceSwap: { media: findShowcaseItem("portrait"), alt: "The target photo for a face swap" },
}
