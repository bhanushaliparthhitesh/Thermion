import { useCallback, useEffect, useState } from 'react'

/**
 * Wraps an async fetcher with the loading/error/empty states every page
 * needs (per the "handle loading, success, empty, error, offline" rule).
 * `deps` re-runs the fetch when it changes; call `refetch()` for manual reloads.
 */
export function useApi(fetcher, deps = [], { isEmpty } = {}) {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('loading') // loading | success | empty | error
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    let cancelled = false
    setStatus('loading')
    fetcher()
      .then((result) => {
        if (cancelled) return
        setData(result)
        const empty = isEmpty ? isEmpty(result) : Array.isArray(result) && result.length === 0
        setStatus(empty ? 'empty' : 'success')
      })
      .catch((err) => {
        if (cancelled) return
        setError(err)
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => load(), [load])

  return { data, status, error, refetch: load }
}
