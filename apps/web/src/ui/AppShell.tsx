import type { ReactNode } from "react"
import { NavLink, Outlet } from "react-router-dom"

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

type AppShellProps = {
  rightSlot?: ReactNode
  outletContext?: unknown
}

export function AppShell({ rightSlot, outletContext }: AppShellProps) {
  return (
    <div className="min-h-screen bg-bg text-text">
      <header className="sticky top-0 z-10 border-b border-border bg-bg/95 backdrop-blur">
        <div className="flex items-center gap-4 overflow-x-auto px-4 py-3 sm:px-6">
          <span className="font-display text-lg text-accent">HIGGSFIELD</span>
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
    </div>
  )
}
