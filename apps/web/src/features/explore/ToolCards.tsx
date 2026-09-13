import { ToolCard } from "./ToolCard"
import { TOOL_CARDS } from "./toolCards"

export function ToolCards() {
  return (
    <ul className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-center gap-x-5 gap-y-1">
      {TOOL_CARDS.map((card) => (
        <li key={card.to}>
          <ToolCard label={card.label} description={card.description} to={card.to} tag={card.tag} />
        </li>
      ))}
    </ul>
  )
}
