import { useCallback, useState } from "react"

export function useLibraryDrawer() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const closeDrawer = useCallback(() => setIsDrawerOpen(false), [])
  const openDrawer = useCallback(() => setIsDrawerOpen(true), [])
  return { isDrawerOpen, openDrawer, closeDrawer }
}
