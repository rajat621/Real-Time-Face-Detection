import { useEffect, useMemo, useRef, useState } from 'react'
import VideoStream from './components/VideoStream'
import ROITable from './components/ROITable'
import useWebSocket from './hooks/useWebSocket'

const defaultApiBase = 'http://localhost:8000'
const apiBase = import.meta.env.VITE_API_BASE_URL || (
  // In local dev (vite on :3000) default to backend on :8000 so websockets target the right host
  window.location.hostname === 'localhost' && window.location.port === '3000'
    ? defaultApiBase
    : ''
)
const ingestWsBase = apiBase.startsWith('https')
  ? apiBase.replace('https', 'wss')
  : apiBase.startsWith('http')
    ? apiBase.replace('http', 'ws')
    : window.location.origin.replace('http', 'ws')

function getSessionId() {
  const existing = window.localStorage.getItem('face-session-id')
  if (existing) return existing
  const created = window.crypto.randomUUID()
  window.localStorage.setItem('face-session-id', created)
  return created
}

export default function App() {
  const sessionId = useMemo(() => getSessionId(), [])
  const [roiRows, setRoiRows] = useState([])
  const [status, setStatus] = useState('No Face')
  const [confidence, setConfidence] = useState(null)
  const [running, setRunning] = useState(false)
  const [cameraReady, setCameraReady] = useState(false)
  const [error, setError] = useState('')
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const timerRef = useRef(null)
  const captureIntervalMs = 100
  const ingestSocket = useWebSocket({
    url: `${ingestWsBase}/feed/ingest?session_id=${sessionId}`,
    onMessage: payload => {
      if (payload.status === 'face_detected') {
        setStatus('Face Detected')
        setConfidence(payload.confidence ?? null)
      } else if (payload.status === 'no_face') {
        setStatus('No Face')
        setConfidence(null)
      } else if (payload.status === 'error') {
        setError(payload.detail || 'An ingest error occurred')
      }
    },
    onError: () => setError('Live ingest connection failed'),
  })

  const streamUrl = `${apiBase}/feed/stream?session_id=${sessionId}`

  async function startCamera() {
    setError('')
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Webcam access is not available in this browser')
      return
    }

    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' },
      audio: false,
    })
    streamRef.current = mediaStream
    if (videoRef.current) {
      videoRef.current.srcObject = mediaStream
      await videoRef.current.play()
    }
    setCameraReady(true)
    setRunning(true)
    console.debug('[App] startCamera: connecting ingest socket')
    ingestSocket.connect()
  }

  function stopCamera() {
    setRunning(false)
    setCameraReady(false)
    ingestSocket.disconnect()
    if (timerRef.current) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  useEffect(() => {
    if (!running || !cameraReady || !videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    timerRef.current = window.setInterval(async () => {
      if (video.readyState < 2) return
      if (!ingestSocket.isOpen()) {
        console.debug('[App] capture loop: socket not open, skipping send')
        return
      }
      canvas.width = video.videoWidth || 1280
      canvas.height = video.videoHeight || 720
      context.drawImage(video, 0, 0, canvas.width, canvas.height)
      canvas.toBlob(async blob => {
        if (!blob || !ingestSocket.isOpen()) return
        const bytes = await blob.arrayBuffer()
        try {
          ingestSocket.send(bytes)
          console.debug('[App] sent frame bytes', bytes.byteLength)
        } catch (e) { console.debug('[App] failed to send frame', e) }
      }, 'image/jpeg', 0.82)
    }, captureIntervalMs)

    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [running, cameraReady, ingestSocket])

  useEffect(() => {
    let cancelled = false

    async function loadRoi() {
      try {
        const response = await fetch(`${apiBase}/roi?session_id=${sessionId}&limit=20&offset=0`)
        if (!response.ok) return
        const payload = await response.json()
        if (!cancelled) {
          setRoiRows(payload.items || [])
        }
      } catch {
        if (!cancelled) {
          setRoiRows([])
        }
      }
    }

    loadRoi()
    const interval = window.setInterval(loadRoi, 2000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [sessionId])

  useEffect(() => () => stopCamera(), [])

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Real-Time Face Detection</p>
          <h1>Live video, ROI storage, and streaming in one containerized flow.</h1>
          <p className="lede">
            Session ID {sessionId.slice(0, 8)} connects webcam capture, MediaPipe face detection, Pillow annotations, and PostgreSQL persistence.
          </p>
        </div>
        <div className="hero-actions">
          <button className="primary" onClick={running ? stopCamera : startCamera}>
            {running ? 'Stop Camera' : 'Start Camera'}
          </button>
          <div className={`badge ${status === 'Face Detected' ? 'badge-good' : 'badge-neutral'}`}>
            {status}{confidence !== null ? ` ${confidence.toFixed(2)}` : ''}
          </div>
        </div>
        {error ? <p className="error-banner">{error}</p> : null}
      </section>

      <section className="workspace">
        <div className="panel stream-panel">
          <VideoStream streamUrl={streamUrl} cameraReady={cameraReady} />
        </div>
        <div className="panel table-panel">
          <ROITable rows={roiRows} />
        </div>
      </section>

      <canvas ref={canvasRef} className="hidden-canvas" />
      <video ref={videoRef} className="hidden-video" playsInline muted />
    </main>
  )
}
