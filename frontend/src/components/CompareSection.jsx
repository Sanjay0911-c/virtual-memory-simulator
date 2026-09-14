const ALGO_ORDER = ['FIFO', 'LRU', 'OPTIMAL']
const ALGO_LABEL = { FIFO: 'FIFO', LRU: 'LRU', OPTIMAL: 'Optimal' }

export default function CompareSection({ compareResult }) {
  if (!compareResult) return null

  return (
    <section className="panel" data-testid="compare-section">
      <h2>Algorithm Comparison</h2>
      <p className="hint">
        Reference string: {compareResult.reference_string.join(', ')} &nbsp;|&nbsp; Frames:{' '}
        {compareResult.frames}
      </p>
      <div className="table-scroll">
        <table className="sim-table">
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Page Faults</th>
              <th>Page Hits</th>
              <th>Hit Ratio</th>
              <th>Fault Ratio</th>
            </tr>
          </thead>
          <tbody>
            {ALGO_ORDER.map((name) => {
              const r = compareResult.results[name]
              return (
                <tr key={name}>
                  <td>{ALGO_LABEL[name]}</td>
                  <td>{r.page_faults}</td>
                  <td>{r.page_hits}</td>
                  <td>{r.hit_ratio}%</td>
                  <td>{r.fault_ratio}%</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
