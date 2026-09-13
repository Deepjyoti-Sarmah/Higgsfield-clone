import { ToolCard } from "./ToolCard"
import { TOOL_CARDS } from "./toolCards"

export function ToolCards() {
  return (
    <ul className="mx-auto grid max-w-5xl grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {TOOL_CARDS.map((card) => (
        <li key={card.to} className="h-full">
          <ToolCard label={card.label} description={card.description} to={card.to} tag={card.tag} />
        </li>
      ))}
    </ul>
  )
}
