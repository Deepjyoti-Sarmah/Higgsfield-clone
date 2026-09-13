import { useCallback } from "react"
import { useSearchParams } from "react-router-dom"
import type { LibraryItem as LibraryItemData } from "../../api/library"

const jobParamKey = "job"

export type LibraryJobParam = {
  selectedJobId: string | null
  selectedItem: LibraryItemData | null
  isMissing: boolean
  selectJob: (id: string) => void
}

export function useLibraryJobParam(items: LibraryItemData[]): LibraryJobParam {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedJobId = searchParams.get(jobParamKey)
  const selectedItem = items.find((item) => item.id === selectedJobId) ?? null

  const selectJob = useCallback(
    (id: string) => {
      setSearchParams({ [jobParamKey]: id }, { replace: true })
    },
    [setSearchParams],
  )

  return {
    selectedJobId,
    selectedItem,
    isMissing: selectedJobId !== null && selectedItem === null,
    selectJob,
  }
}
