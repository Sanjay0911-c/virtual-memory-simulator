export default function SimulationTable({ result }) {
  if (!result) return null

  const frameCount = result.steps[0]?.frames.length ?? 0
  const frameHeaders = Array.from({ length: frameCount }, (_, i) => `Frame ${i + 1}`)

  return (
    <section className="panel" data-testid="simulation-table">
      <h2>Step-by-Step Simulation</h2>
      <div className="table-scroll">
        <table className="sim-table">
          <thead>
            <tr>
              <th>Step</th>
              <th>Page</th>
              {frameHeaders.map((h) => (
                <th key={h}>{h}</th>
              ))}
              <th>Result</th>
              <th>Replaced</th>
            </tr>
          </thead>
          <tbody>
            {result.steps.map((step) => (
              <tr key={step.step} className={step.result === 'FAULT' ? 'row-fault' : 'row-hit'}>
                <td>{step.step}</td>
                <td>{step.page}</td>
                {step.frames.map((f, idx) => (
                  <td key={idx}>{f === null ? '—' : f}</td>
                ))}
                <td>
                  <span className={`badge ${step.result === 'FAULT' ? 'badge-fault' : 'badge-hit'}`}>
                    {step.result === 'FAULT' ? 'PAGE FAULT' : 'HIT'}
                  </span>
                </td>
                <td>{step.replaced_page === null ? '—' : step.replaced_page}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
