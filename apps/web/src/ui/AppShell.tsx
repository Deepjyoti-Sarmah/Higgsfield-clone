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
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent font-display text-lg text-accent-ink"
    >
      H
    </span>
  )
}

function AppFooter() {
  return (
    <footer className="border-t border-border">
      <div className="flex flex-col gap-4 px-4 py-8 sm:px-6">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <span className="font-display text-lg uppercase text-text">Higgsfield</span>
          {navItems.map((item) => (
            <Link key={item.to} to={item.to} className="text-sm text-muted hover:text-text">
              {item.label}
            </Link>
          ))}
        </div>
        <p className="text-xs text-muted">Demo rebuild for evaluation — not affiliated with Higgsfield AI.</p>
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
        <div className="flex items-center gap-4 overflow-x-auto px-4 py-3 sm:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2" aria-label="Higgsfield home">
            <BrandMark />
            <span className="font-display text-lg uppercase tracking-wide text-text">Higgsfield</span>
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
