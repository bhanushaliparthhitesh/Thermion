const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:3000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

export async function apiFetch(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (err) {
    // Network-level failure — backend unreachable, not just a bad response.
    throw new ApiError('Backend unavailable. Is `sam local start-api` running?', 0)
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.error || detail
    } catch {
      // body wasn't JSON — fall back to statusText
    }
    throw new ApiError(detail, res.status)
  }

  return res.json()
}
