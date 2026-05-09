export default function VideoStream({ streamUrl, cameraReady }) {
  return (
    <div className="stream-card">
      <div className="section-heading">
        <div>
          <p className="section-label">Live Stream</p>
          <h2>Processed feed</h2>
        </div>
        <span className={`stream-pill ${cameraReady ? 'stream-pill-live' : ''}`}>{cameraReady ? 'Streaming' : 'Idle'}</span>
      </div>
      <div className="stream-frame">
        <img src={streamUrl} alt="Live processed camera feed" />
      </div>
    </div>
  )
}
