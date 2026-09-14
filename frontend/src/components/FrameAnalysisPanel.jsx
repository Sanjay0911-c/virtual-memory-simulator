export default function FrameAnalysisPanel({
  minFramesInput,
  onMinFramesChange,
  maxFramesInput,
  onMaxFramesChange,
  onAnalyze,
  loading,
}) {
  return (
    <section className="panel">
      <h2>Frame-Count Analysis</h2>
      <p className="hint">
        Uses the page reference string above. Runs FIFO, LRU, and Optimal across a range
        of frame counts and checks the FIFO results for Belady's anomaly.
      </p>

      <div className="field-row">
        <div className="field">
          <label htmlFor="min-frames">Min Frames</label>
          <input
            id="min-frames"
            type="number"
            min="1"
            placeholder="e.g. 2"
            value={minFramesInput}
            onChange={(e) => onMinFramesChange(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="max-frames">Max Frames</label>
          <input
            id="max-frames"
            type="number"
            min="1"
            placeholder="e.g. 6"
            value={maxFramesInput}
            onChange={(e) => onMaxFramesChange(e.target.value)}
          />
        </div>
      </div>

      <div className="button-row">
        <button className="btn btn-primary" onClick={onAnalyze} disabled={loading}>
          {loading ? 'Analyzing…' : 'Analyze Frame Range'}
        </button>
      </div>
    </section>
  )
}
