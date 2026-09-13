export type ToolCard = {
  label: string
  description: string
  to: string
}

export const TOOL_CARDS: ToolCard[] = [
  {
    label: "Explore",
    description: "Browse every effect and start creating.",
    to: "/",
  },
  {
    label: "Create video",
    description: "Turn a photo into a 5-second clip.",
    to: "/create/video",
  },
  {
    label: "Create image",
    description: "Generate images from a prompt.",
    to: "/create/image",
  },
  {
    label: "Library",
    description: "Every generation from this session.",
    to: "/library",
  },
  {
    label: "Credits",
    description: "Your balance and top-ups.",
    to: "/credits",
  },
]
