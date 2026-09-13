import { useOutletContext } from "react-router-dom"
import { useCreditsPage } from "../../api/credits"
import type { SessionContextValue } from "../session/useSession"
import { CreditsBalanceCard } from "./CreditsBalanceCard"
import { creditsCopy } from "./creditsCopy"
import { CreditsTopUpCard } from "./CreditsTopUpCard"

export function CreditsPage() {
  const session = useOutletContext<SessionContextValue>()
  const state = useCreditsPage(session)

  return (
    <section className="mx-auto flex w-full max-w-2xl flex-col gap-8 py-4">
      <header className="flex flex-col gap-2">
        <h1 className="text-4xl leading-none text-text sm:text-5xl">{creditsCopy.page.title}</h1>
        <p className="max-w-xl text-muted">{creditsCopy.page.subtitle}</p>
      </header>
      <CreditsBalanceCard
        status={state.balanceStatus}
        balance={state.balance}
        onRetry={state.reload}
      />
      <CreditsTopUpCard
        status={state.topUpStatus}
        amount={state.grantedAmount}
        balance={state.balance}
        onTopUp={state.topUp}
      />
    </section>
  )
}
