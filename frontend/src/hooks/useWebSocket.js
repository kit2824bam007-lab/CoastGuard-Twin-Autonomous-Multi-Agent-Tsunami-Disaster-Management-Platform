import { useEffect, useRef, useState, useCallback } from 'react'

// Auto-reconnecting WebSocket hook for the live alert stream.
export function useAlertsWebSocket(url, onMessage) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const retryRef = useRef(1000) // ms, exponential backoff up to 30s

  const connect = useCallback(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retryRef.current = 1000
    }
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        onMessage(payload)
      } catch (e) {
        console.error('Bad WS payload', e)
      }
    }
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, retryRef.current)
      retryRef.current = Math.min(retryRef.current * 2, 30000)
    }
    ws.onerror = () => ws.close()
  }, [url, onMessage])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])

  return { connected }
}
