export type ToolCard = {
  label: string
  description: string
  to: string
  tag: string
}

export const TOOL_CARDS: ToolCard[] = [
  {
    label: "Explore",
    description: "Browse every effect and start creating.",
    to: "/",
    tag: "Gallery",
  },
  {
    label: "Create video",
    description: "Turn a photo into a 5-second clip.",
    to: "/create/video",
    tag: "Video",
  },
  {
    label: "Create image",
    description: "Generate images from a prompt.",
    to: "/create/image",
    tag: "Image",
  },
  {
    label: "Library",
    description: "Every generation from this session.",
    to: "/library",
    tag: "History",
  },
  {
    label: "Credits",
    description: "Your balance and top-ups.",
    to: "/credits",
    tag: "Balance",
  },
]
