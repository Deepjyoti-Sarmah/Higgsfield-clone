import { buttonClasses } from "../../ui/buttonStyles"
import { Button } from "../../ui/Button"
import { GenerationBadge } from "../../ui/GenerationBadge"
import { imageCreateCopy } from "./imageCreateCopy"

type ImageResultGridProps = {
  imageUrls: string[]
  prompt: string
  backend: string | null
  onMakeAnother: () => void
}

const PLACEHOLDER_BACKENDS = ["mock", "local-motion", "placeholder"]

export function ImageResultGrid({
  imageUrls,
  prompt,
  backend,
  onMakeAnother,
}: ImageResultGridProps) {
  const copy = imageCreateCopy
  const isPlaceholder = backend !== null && PLACEHOLDER_BACKENDS.includes(backend)
  return (
    <div className="flex w-full flex-col items-center gap-4">
      <GenerationBadge generatedBy={backend} kind="image" />
      <ul className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
        {imageUrls.map((url, index) => (
          <li key={url} className="flex flex-col items-stretch gap-2">
            <div className="aspect-square w-full overflow-hidden rounded-xl border border-border">
              <img
                src={url}
                alt={copy.result.imageAlt(index + 1, prompt)}
                className="h-full w-full object-cover"
              />
            </div>
            <a href={url} download className={`${buttonClasses("secondary")} self-start`}>
              {copy.result.download}
            </a>
          </li>
        ))}
      </ul>
      {isPlaceholder && <p className="text-xs text-muted">{copy.result.placeholderNotice}</p>}
      <Button variant="secondary" onClick={onMakeAnother}>
        {copy.result.makeAnother}
      </Button>
    </div>
  )
}
