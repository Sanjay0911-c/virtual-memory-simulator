/**
 * Purely a renderer for what /api/frame-analysis already returned — no
 * fault-counting or anomaly-detection logic lives here. The backend's
 * belady_anomaly.detected/occurrences/explanation are displayed as-is.
 */
export default function FrameAnalysisResults({ analysis }) {
  if (!analysis) return null

  const { sweep, belady_anomaly: belady } = analysis

  return (
    <section className="panel" data-testid="frame-analysis-results">
      <h2>Frame-Count Analysis Results</h2>
      <p className="hint">
        Reference string: {analysis.reference_string.join(', ')} &nbsp;|&nbsp; Frames{' '}
        {analysis.min_frames}–{analysis.max_frames}
      </p>

      <div className="table-scroll">
        <table className="sim-table">
          <thead>
            <tr>
              <th>Frames</th>
              <th>FIFO Faults</th>
              <th>LRU Faults</th>
              <th>Optimal Faults</th>
            </tr>
          </thead>
          <tbody>
            {sweep.map((row) => (
              <tr key={row.frames} data-testid={`frame-analysis-row-${row.frames}`}>
                <td>{row.frames}</td>
                <td>{row.results.FIFO.page_faults}</td>
                <td>{row.results.LRU.page_faults}</td>
                <td>{row.results.OPTIMAL.page_faults}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        className={`belady-panel ${belady.detected ? 'belady-detected' : 'belady-clear'}`}
        data-testid="belady-panel"
      >
        <h3>
          {belady.detected
            ? "⚠ Belady's Anomaly Detected (FIFO)"
            : "✓ No Belady's Anomaly Detected (FIFO)"}
        </h3>
        <p>{belady.explanation}</p>
        {belady.detected && (
          <ul className="belady-occurrences" data-testid="belady-occurrences">
            {belady.occurrences.map((occ, idx) => (
              <li key={idx}>
                Increasing frames from {occ.from_frames} to {occ.to_frames} increased FIFO
                page faults from {occ.from_faults} to {occ.to_faults}.
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
