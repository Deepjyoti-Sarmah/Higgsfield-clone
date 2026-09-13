import type { components } from "./generated/schema"

export type JobStatus = components["schemas"]["JobStatusEvent"]["status"]

export const TERMINAL_JOB_STATUSES: readonly JobStatus[] = ["succeeded", "failed"]

export function isTerminalJobStatus(status: JobStatus): boolean {
  return TERMINAL_JOB_STATUSES.includes(status)
}
