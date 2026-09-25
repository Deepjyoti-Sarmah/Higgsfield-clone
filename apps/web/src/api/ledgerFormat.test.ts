import { describe, expect, it } from "vitest"
import { ledgerAmount, ledgerAmountTone, ledgerKindLabel, relativeTime } from "./ledgerFormat"

describe("ledger kind labels", () => {
  it("maps API kinds onto user words", () => {
    expect(ledgerKindLabel("HOLD")).toBe("Hold")
    expect(ledgerKindLabel("SETTLE")).toBe("Settled")
    expect(ledgerKindLabel("RELEASE")).toBe("Refund")
    expect(ledgerKindLabel("TOPUP")).toBe("Top-up")
    expect(ledgerKindLabel("GRANT")).toBe("Welcome grant")
  })
})

describe("ledger amounts", () => {
  it("formats holds as minus and refunds as plus", () => {
    expect(ledgerAmount(-20)).toBe("\u221220")
    expect(ledgerAmount(20)).toBe("+20")
    expect(ledgerAmount(0)).toBe("0")
  })

  it("tones positives success, negatives text, zero muted", () => {
    expect(ledgerAmountTone(20)).toBe("success")
    expect(ledgerAmountTone(-20)).toBe("text")
    expect(ledgerAmountTone(0)).toBe("muted")
  })
})

describe("relative time", () => {
  const now = new Date("2026-09-26T12:00:00Z")

  it("formats recent times", () => {
    expect(relativeTime("2026-09-26T11:59:30Z", now)).toBe("just now")
    expect(relativeTime("2026-09-26T11:30:00Z", now)).toBe("30m ago")
    expect(relativeTime("2026-09-26T09:00:00Z", now)).toBe("3h ago")
    expect(relativeTime("2026-09-24T12:00:00Z", now)).toBe("2d ago")
  })

  it("returns nothing for garbage input", () => {
    expect(relativeTime("not-a-date", now)).toBe("")
  })
})
