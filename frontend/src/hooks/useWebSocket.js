import { useEffect, useRef } from 'react'

export default function useWebSocket({ url, onMessage, onError }) {
  const socketRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)
  const apiRef = useRef(null)

  useEffect(() => {
    onMessageRef.current = onMessage
    onErrorRef.current = onError
  }, [onMessage, onError])

  const connect = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      return socketRef.current
    }
    console.debug('[useWebSocket] connecting to', url)
    const socket = new WebSocket(url)
    socket.binaryType = 'arraybuffer'
    // Expose the last-created socket for debugging in dev (inspected from page)
    try { window.__lastIngestSocket = socket } catch (e) { /* ignore in non-browser env */ }
    socket.onopen = () => console.debug('[useWebSocket] open', url)
    socket.onclose = e => console.debug('[useWebSocket] close', e.code, e.reason)
    socket.onmessage = event => {
      try {
        const data = JSON.parse(event.data)
        onMessageRef.current?.(data)
      } catch {
        onMessageRef.current?.({ status: 'error', detail: 'Invalid websocket payload' })
      }
    }
    socket.onerror = () => {
      onErrorRef.current?.()
    }
    socketRef.current = socket
    return socket
  }

  const disconnect = () => {
    if (socketRef.current) {
      console.debug('[useWebSocket] disconnecting')
      try { socketRef.current.close() } catch(e) {}
      socketRef.current = null
    }
  }

  const send = payload => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.debug('[useWebSocket] send skipped, socket not open')
      return
    }
    try {
      socketRef.current.send(payload)
    } catch (e) { console.debug('[useWebSocket] send error', e) }
  }

  const isOpen = () => socketRef.current?.readyState === WebSocket.OPEN

  useEffect(() => () => disconnect(), [])

  if (!apiRef.current) {
    apiRef.current = { connect, disconnect, send, isOpen }
  }

  return apiRef.current
}
