import type { ReactNode } from "react"
import { Link, Outlet } from "react-router-dom"
import { BrandMark, BrandWordmark } from "./BrandMark"

type AppShellProps = {
  rightSlot?: ReactNode
  creditsSlot?: ReactNode
  outletContext?: unknown
  fullBleed?: boolean
  hideFooter?: boolean
}

function ShellFooter() {
  return (
    <footer className="border-t border-border px-4 py-4 text-xs text-muted sm:px-6">
      Reel &amp; Still · a small studio for short films
    </footer>
  )
}

export function AppShell({ rightSlot, creditsSlot, outletContext, fullBleed = false, hideFooter = false }: AppShellProps) {
  return (
    <div className="flex min-h-dvh flex-col bg-bg text-text">
      <header className="sticky top-0 z-20 h-14 shrink-0 border-b border-border bg-bg/95 backdrop-blur">
        <div className="flex h-full items-center gap-4 px-4 sm:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2" aria-label="Reel & Still home">
            <BrandMark className="h-6 w-6 text-accent" />
            <BrandWordmark />
          </Link>
          <nav className="flex items-center gap-1" aria-label="Tools">
            <Link
              to="/studio"
              className="shrink-0 whitespace-nowrap rounded-md px-2 py-1 text-sm font-medium text-muted transition-colors hover:text-text"
            >
              Studio
            </Link>
            <Link
              to="/studio?tab=faceswap"
              className="hidden shrink-0 whitespace-nowrap rounded-md px-2 py-1 text-sm font-medium text-muted transition-colors hover:text-text md:inline-flex"
            >
              Face swap
            </Link>
          </nav>
          <div className="ml-auto flex items-center gap-3">
            {creditsSlot}
            {rightSlot}
          </div>
        </div>
      </header>
      <main className={fullBleed ? "flex min-h-0 flex-1 flex-col" : "flex-1 px-4 py-10 sm:px-6"}>
        <Outlet context={outletContext} />
      </main>
      {!hideFooter && <ShellFooter />}
    </div>
  )
}
