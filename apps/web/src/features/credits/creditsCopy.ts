export function balanceValue(balance: number): string {
  return `${balance} credits`
}

export function topUpAction(amount: number): string {
  return `Add ${amount} credits`
}

export function topUpDone(amount: number, balance: number): string {
  return `Added ${amount} credits. New balance: ${balance}.`
}

export const creditsCopy = {
  page: {
    title: "Credits",
    subtitle: "Your balance and how to top it up.",
  },
  balance: {
    label: "Balance",
    value: balanceValue,
  },
  states: {
    loading: {
      srText: "Loading your credits",
    },
    error: {
      title: "We couldn't load your credits.",
      body: "Check your connection and try again.",
      action: "Retry",
    },
  },
  topup: {
    title: "Add credits",
    description: "This is a demo top-up. No payment is taken.",
    action: topUpAction,
    pending: "Adding credits...",
    done: topUpDone,
    error: "We couldn't add credits.",
    retry: "Try again",
  },
}
