type SequenceStepProps = {
  number: string
  heading: string
  body: string
  children: React.ReactNode
}

// Numbered shell for one step of the sequence flow.
export function SequenceStep({ number, heading, body, children }: SequenceStepProps) {
  return (
    <section aria-label={`Step ${number}: ${heading}`} className="flex flex-col gap-2 rounded-xl border border-border bg-surface p-3">
      <div className="flex items-baseline gap-2">
        <span aria-hidden="true" className="font-mono text-[11px] text-muted">{number}</span>
        <h3 className="text-[13px] font-semibold text-text">{heading}</h3>
      </div>
      <p className="text-[13px] text-faint">{body}</p>
      {children}
    </section>
  )
}
