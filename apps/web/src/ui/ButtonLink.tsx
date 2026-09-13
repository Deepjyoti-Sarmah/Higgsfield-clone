import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import { buttonClasses, type ButtonVariant } from "./buttonStyles"

type ButtonLinkProps = {
  to: string
  variant?: ButtonVariant
  className?: string
  children: ReactNode
}

export function ButtonLink({
  to,
  variant = "primary",
  className = "",
  children,
}: ButtonLinkProps) {
  return (
    <Link to={to} className={`${buttonClasses(variant)} ${className}`}>
      {children}
    </Link>
  )
}
