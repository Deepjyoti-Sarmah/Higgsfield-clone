import type { ReactNode } from "react"
import { Link, NavLink, Outlet } from "react-router-dom"

const navItems = [
  { to: "/", label: "Explore" },
  { to: "/create/video", label: "Create video" },
  { to: "/create/image", label: "Create image" },
  { to: "/library", label: "Library" },
  { to: "/credits", label: "Credits" },
]

function navLinkClasses({ isActive }: { isActive: boolean }) {
  const base = "whitespace-nowrap px-3 py-2 text-sm font-medium transition-colors"
  return isActive ? `${base} text-accent` : `${base} text-muted hover:text-text`
}

function BrandMark() {
  return (
    <span
      aria-hidden="true"
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-accent text-accent-ink shadow-md shadow-accent/20 transition-transform hover:scale-105"
    >
      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path d="M18.35 9.84L18.33 9.66C18.18 7.93 17.1 4.69 14.08 4.69C11.84 4.69 10.15 6.97 8.66 8.98C7.47 10.59 6.44 11.97 5.31 11.97C5.01 11.94 4.62 11.78 4.38 11.43C4.16 11.11 4.11 10.7 4.22 10.21C4.39 9.44 5.39 8.72 6.45 7.95C7.03 7.54 7.62 7.11 8.04 6.69C9.23 5.51 9.83 4.65 9.83 3.27C9.83 1.89 9.09 1.21 8.47 0.91C7.24 0.32 5.42 0.67 4.26 1.7C4.09 1.86 3.91 2.01 3.75 2.16C2.59 3.23 1.8 3.96 0 3.4V5.64C2.39 6.73 4.4 4.65 5.16 3.7C5.74 3.07 6.36 2.7 6.82 2.7H6.85C7.05 2.71 7.23 2.79 7.35 2.94C7.56 3.18 7.64 3.47 7.6 3.79C7.51 4.46 6.84 5.24 5.6 6.1C4.15 7.1 1.72 8.78 1.53 10.9C1.39 12.42 2.15 13.94 3.34 14.52C6.12 15.88 7.81 13.54 9.6 11.08C10.97 9.18 12.27 7.37 14.08 7.37C15.71 7.37 16.31 8.76 16.31 9.63V9.8L16.15 9.84C12.21 10.56 10.06 14.36 10.06 16.12C10.06 17.87 11.5 19.38 13.28 19.38C15.36 19.38 17.93 17.55 18.34 12.4L18.36 12.21H20V9.84H18.35ZM16.2 12.47C15.88 15.55 14.35 16.99 13.42 16.99C13 16.99 12.42 16.63 12.42 15.96C12.42 15.21 13.5 12.93 15.95 12.25L16.23 12.18L16.2 12.47Z" />
      </svg>
    </span>
  )
}

function AppFooter() {
  return (
    <footer className="border-t border-border">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 px-4 py-4 text-xs text-muted sm:px-6">
        <span className="font-display uppercase text-text">Higgsfield</span>
        {navItems.map((item) => (
          <Link key={item.to} to={item.to} className="hover:text-text">
            {item.label}
          </Link>
        ))}
        <span className="ml-auto">Demo rebuild for evaluation — not affiliated with Higgsfield AI.</span>
      </div>
    </footer>
  )
}

type AppShellProps = {
  rightSlot?: ReactNode
  outletContext?: unknown
}

export function AppShell({ rightSlot, outletContext }: AppShellProps) {
  return (
    <div className="min-h-screen bg-bg text-text">
      <header className="sticky top-0 z-10 border-b border-border bg-bg/95 backdrop-blur">
        <div className="flex items-center gap-4 overflow-x-auto px-4 py-2 sm:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2" aria-label="Higgsfield home">
            <BrandMark />
            <span className="font-display text-base uppercase tracking-wide text-text">Higgsfield</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={navLinkClasses} end={item.to === "/"}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">{rightSlot}</div>
        </div>
      </header>
      <main className="px-4 py-10 sm:px-6">
        <Outlet context={outletContext} />
      </main>
      <AppFooter />
    </div>
  )
}
