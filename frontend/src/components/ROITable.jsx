export default function ROITable({ rows }) {
  return (
    <div className="table-card">
      <div className="section-heading">
        <div>
          <p className="section-label">ROI Data</p>
          <h2>Latest detections</h2>
        </div>
        <span className="stream-pill">{rows.length} rows</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Session</th>
              <th>Frame</th>
              <th>Timestamp</th>
              <th>X Min</th>
              <th>Y Min</th>
              <th>X Max</th>
              <th>Y Max</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map(row => (
                <tr key={row.id}>
                  <td>{String(row.session_id).slice(0, 8)}</td>
                  <td>{row.frame_index}</td>
                  <td>{new Date(row.timestamp).toLocaleTimeString()}</td>
                  <td>{row.x_min}</td>
                  <td>{row.y_min}</td>
                  <td>{row.x_max}</td>
                  <td>{row.y_max}</td>
                  <td>{row.confidence == null ? 'n/a' : row.confidence.toFixed(2)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="8" className="empty-state">
                  No detections yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
