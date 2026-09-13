export type ButtonVariant = "primary" | "secondary"

const baseClasses =
  "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold " +
  "transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent " +
  "disabled:cursor-not-allowed disabled:opacity-60"

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-accent text-accent-ink shadow-lg shadow-accent/20 hover:bg-accent/90",
  secondary: "bg-surface text-text border border-border hover:border-accent/60",
}

export function buttonClasses(variant: ButtonVariant = "primary"): string {
  return `${baseClasses} ${variantClasses[variant]}`
}
