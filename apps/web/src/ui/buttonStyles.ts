export type ButtonVariant = "primary" | "secondary" | "ghost"

const baseClasses =
  "inline-flex items-center justify-center gap-2 rounded-[10px] px-4 text-sm font-medium " +
  "h-10 transition-all duration-150 active:scale-[0.98] " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent " +
  "disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-accent text-accent-ink hover:bg-accent/90",
  secondary: "bg-surface text-text border border-border hover:border-accent/60",
  ghost: "text-muted hover:text-text",
}

export function buttonClasses(variant: ButtonVariant = "primary"): string {
  return `${baseClasses} ${variantClasses[variant]}`
}
