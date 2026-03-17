import { useEffect, useRef } from 'react'

export function useSSE(onEvent) {
  const cbRef = useRef(onEvent)
  useEffect(() => { cbRef.current = onEvent })

  useEffect(() => {
    const es = new EventSource('/api/v1/events')
    es.onmessage = (e) => {
      try { cbRef.current(JSON.parse(e.data)) } catch {}
    }
    return () => es.close()
  }, [])
}
