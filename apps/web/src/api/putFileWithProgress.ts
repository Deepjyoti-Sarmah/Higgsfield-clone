export class UploadHttpError extends Error {
  readonly status: number

  constructor(status: number, url: string) {
    super(`Upload to storage failed with status ${status} for ${url}`)
    this.name = "UploadHttpError"
    this.status = status
  }
}

export type PutFileOptions = {
  url: string
  file: File
  headers: Record<string, string>
  signal: AbortSignal
  onProgress: (fraction: number) => void
}

// XHR, not fetch: openapi-fetch cannot report upload progress. The signature
// covers Content-Type, so exactly `headers` (and nothing else) is sent.
export function putFileWithProgress({
  url,
  file,
  headers,
  signal,
  onProgress,
}: PutFileOptions): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open("PUT", url)
    for (const [name, value] of Object.entries(headers)) {
      request.setRequestHeader(name, value)
    }
    request.withCredentials = false
    request.upload.onprogress = (event) => {
      onProgress(event.total > 0 ? event.loaded / event.total : 0)
    }
    request.onload = () => {
      if (request.status >= 200 && request.status < 300) resolve()
      else reject(new UploadHttpError(request.status, url))
    }
    request.onerror = () => reject(new UploadHttpError(0, url))
    request.onabort = () => reject(new DOMException("Upload aborted", "AbortError"))
    signal.addEventListener("abort", () => request.abort(), { once: true })
    request.send(file)
  })
}
