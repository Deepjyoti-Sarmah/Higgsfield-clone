import type { RefObject } from "react"

type CanvasHeadingProps = {
  text: string
  headingRef: RefObject<HTMLHeadingElement | null>
}

export function CanvasHeading({ text, headingRef }: CanvasHeadingProps) {
  return (
    <h2
      ref={headingRef}
      tabIndex={-1}
      className="text-center text-2xl text-text focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent"
    >
      {text}
    </h2>
  )
}
