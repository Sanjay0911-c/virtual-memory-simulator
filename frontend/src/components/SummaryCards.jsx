export default function SummaryCards({ result }) {
  if (!result) return null

  const cards = [
    { label: 'Total Requests', value: result.total_requests },
    { label: 'Page Faults', value: result.page_faults },
    { label: 'Page Hits', value: result.page_hits },
    { label: 'Hit Ratio', value: `${result.hit_ratio}%` },
    { label: 'Fault Ratio', value: `${result.fault_ratio}%` },
    { label: 'Replacements', value: result.replacements },
  ]

  return (
    <section className="panel" data-testid="summary-cards">
      <h2>Results — {result.algorithm}</h2>
      <div className="cards-grid">
        {cards.map((c) => (
          <div className="card" key={c.label}>
            <div className="card-value">{c.value}</div>
            <div className="card-label">{c.label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
