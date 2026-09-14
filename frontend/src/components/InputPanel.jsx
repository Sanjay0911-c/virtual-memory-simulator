export default function InputPanel({
  referenceInput,
  onReferenceChange,
  framesInput,
  onFramesChange,
  algorithm,
  onAlgorithmChange,
  onSimulate,
  onCompare,
  onReset,
  loading,
}) {
  return (
    <section className="panel input-panel">
      <div className="field">
        <label htmlFor="reference">Page Reference String</label>
        <input
          id="reference"
          type="text"
          placeholder="e.g. 7,0,1,2,0,3,0,4,2,3"
          value={referenceInput}
          onChange={(e) => onReferenceChange(e.target.value)}
        />
        <p className="hint">Comma- or space-separated non-negative integers.</p>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="frames">Number of Frames</label>
          <input
            id="frames"
            type="number"
            min="1"
            placeholder="e.g. 3"
            value={framesInput}
            onChange={(e) => onFramesChange(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="algorithm">Algorithm</label>
          <select id="algorithm" value={algorithm} onChange={(e) => onAlgorithmChange(e.target.value)}>
            <option value="FIFO">FIFO</option>
            <option value="LRU">LRU</option>
            <option value="OPTIMAL">Optimal</option>
          </select>
        </div>
      </div>

      <div className="button-row">
        <button className="btn btn-primary" onClick={onSimulate} disabled={loading}>
          {loading ? 'Running…' : 'Simulate'}
        </button>
        <button className="btn btn-secondary" onClick={onCompare} disabled={loading}>
          Compare Algorithms
        </button>
        <button className="btn btn-ghost" onClick={onReset} disabled={loading}>
          Reset
        </button>
      </div>
    </section>
  )
}
