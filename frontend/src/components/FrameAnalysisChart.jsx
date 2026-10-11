/**
 * Inline-SVG line chart of page faults vs. frame count for FIFO, LRU and
 * Optimal. Pure renderer: every number comes from the /api/frame-analysis
 * response (sweep[].results[ALGO].page_faults). Belady's anomaly points are
 * taken from belady_anomaly.occurrences as returned by the backend — nothing
 * is recomputed here.
 */
const SERIES = [
  { key: 'FIFO', label: 'FIFO', color: '#dc2626', shape: 'circle' },
  { key: 'LRU', label: 'LRU', color: '#2563eb', shape: 'square' },
  { key: 'OPTIMAL', label: 'Optimal', color: '#16a34a', shape: 'diamond' },
]

const W = 640
const H = 360
const M = { top: 20, right: 24, bottom: 52, left: 52 }
const PLOT_W = W - M.left - M.right
const PLOT_H = H - M.top - M.bottom

function niceTicks(maxValue) {
  // Integer ticks from 0; at most ~6 intervals.
  const top = Math.max(1, maxValue)
  const step = Math.max(1, Math.ceil(top / 6))
  const ticks = []
  for (let v = 0; v < top + step; v += step) {
    ticks.push(v)
    if (v >= top) break
  }
  return ticks
}

function Marker({ shape, x, y, color }) {
  const common = { fill: color, stroke: '#ffffff', strokeWidth: 1.5 }
  if (shape === 'square') {
    return <rect x={x - 5} y={y - 5} width={10} height={10} {...common} />
  }
  if (shape === 'diamond') {
    return <polygon points={`${x},${y - 7} ${x + 7},${y} ${x},${y + 7} ${x - 7},${y}`} {...common} />
  }
  return <circle cx={x} cy={y} r={5.5} {...common} />
}

export default function FrameAnalysisChart({ analysis }) {
  if (!analysis || !analysis.sweep || analysis.sweep.length === 0) return null

  const { sweep, belady_anomaly: belady } = analysis
  const frameCounts = sweep.map((row) => row.frames)
  const minF = frameCounts[0]
  const maxF = frameCounts[frameCounts.length - 1]

  const maxFaults = Math.max(
    ...sweep.flatMap((row) => SERIES.map((s) => row.results[s.key].page_faults)),
  )
  const yTicks = niceTicks(maxFaults)
  const yMax = yTicks[yTicks.length - 1]

  // Single frame count: centre the lone point instead of dividing by zero.
  const xFor = (frames) =>
    maxF === minF ? M.left + PLOT_W / 2 : M.left + ((frames - minF) / (maxF - minF)) * PLOT_W
  const yFor = (faults) => M.top + PLOT_H - (faults / yMax) * PLOT_H

  // Frames whose FIFO point is the "increased" end of a backend-reported occurrence.
  const anomalyOccurrences = belady?.detected ? belady.occurrences : []
  const anomalyFrames = new Set(anomalyOccurrences.map((o) => o.to_frames))

  const xLabelStep = Math.max(1, Math.ceil(frameCounts.length / 12))

  const description = [
    `Line chart of page faults versus number of frames, from ${minF} to ${maxF} frames.`,
    ...sweep.map(
      (row) =>
        `${row.frames} frames: ` +
        SERIES.map((s) => `${s.label} ${row.results[s.key].page_faults} faults`).join(', ') +
        '.',
    ),
    anomalyOccurrences.length > 0
      ? "Belady's anomaly detected for FIFO: " +
        anomalyOccurrences
          .map(
            (o) =>
              `from ${o.from_frames} to ${o.to_frames} frames, faults rose from ${o.from_faults} to ${o.to_faults}`,
          )
          .join('; ') +
        '.'
      : "No Belady's anomaly detected for FIFO.",
  ].join(' ')

  return (
    <div className="chart-wrap" data-testid="frame-analysis-chart">
      <h3>Page Faults vs. Frame Count</h3>
      <svg
        className="fa-chart"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-labelledby="fa-chart-title fa-chart-desc"
      >
        <title id="fa-chart-title">Page faults versus frame count for FIFO, LRU and Optimal</title>
        <desc id="fa-chart-desc">{description}</desc>

        {/* Y grid, ticks and labels (zero-based) */}
        {yTicks.map((t) => (
          <g key={`y-${t}`}>
            <line x1={M.left} x2={W - M.right} y1={yFor(t)} y2={yFor(t)} className="chart-grid" />
            <text x={M.left - 8} y={yFor(t) + 4} textAnchor="end" className="chart-tick">
              {t}
            </text>
          </g>
        ))}

        {/* Axes */}
        <line x1={M.left} x2={M.left} y1={M.top} y2={M.top + PLOT_H} className="chart-axis" />
        <line
          x1={M.left}
          x2={W - M.right}
          y1={M.top + PLOT_H}
          y2={M.top + PLOT_H}
          className="chart-axis"
        />

        {/* X ticks and labels */}
        {frameCounts.map((f, idx) =>
          idx % xLabelStep === 0 || idx === frameCounts.length - 1 ? (
            <text key={`x-${f}`} x={xFor(f)} y={M.top + PLOT_H + 18} textAnchor="middle" className="chart-tick">
              {f}
            </text>
          ) : null,
        )}
        <text x={M.left + PLOT_W / 2} y={H - 8} textAnchor="middle" className="chart-label">
          Number of frames
        </text>
        <text
          transform={`translate(14 ${M.top + PLOT_H / 2}) rotate(-90)`}
          textAnchor="middle"
          className="chart-label"
        >
          Page faults
        </text>

        {/* Lines */}
        {SERIES.map((s) =>
          sweep.length > 1 ? (
            <polyline
              key={`line-${s.key}`}
              fill="none"
              stroke={s.color}
              strokeWidth={2}
              points={sweep.map((row) => `${xFor(row.frames)},${yFor(row.results[s.key].page_faults)}`).join(' ')}
            />
          ) : null,
        )}

        {/* Belady's anomaly highlights (FIFO points where faults rose) */}
        {sweep
          .filter((row) => anomalyFrames.has(row.frames))
          .map((row) => {
            const x = xFor(row.frames)
            const y = yFor(row.results.FIFO.page_faults)
            return (
              <g key={`anomaly-${row.frames}`} data-testid={`belady-marker-${row.frames}`}>
                <circle cx={x} cy={y} r={13} fill="none" stroke="#b91c1c" strokeWidth={2.5} strokeDasharray="4 3" />
                <text x={x} y={y - 18} textAnchor="middle" className="chart-anomaly-label">
                  Belady's anomaly
                </text>
              </g>
            )
          })}

        {/* Point markers, drawn last so they sit on top; native tooltips via <title> */}
        {SERIES.map((s) =>
          sweep.map((row) => {
            const faults = row.results[s.key].page_faults
            return (
              <g key={`pt-${s.key}-${row.frames}`}>
                <title>{`${s.label}, ${row.frames} frames: ${faults} faults`}</title>
                <Marker shape={s.shape} x={xFor(row.frames)} y={yFor(faults)} color={s.color} />
              </g>
            )
          }),
        )}
      </svg>

      <ul className="chart-legend" aria-label="Chart legend">
        {SERIES.map((s) => (
          <li key={s.key}>
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
              <Marker shape={s.shape} x={9} y={9} color={s.color} />
            </svg>
            {s.label}
          </li>
        ))}
        <li>
          <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
            <circle cx={9} cy={9} r={7} fill="none" stroke="#b91c1c" strokeWidth={2} strokeDasharray="3 2" />
          </svg>
          Belady's anomaly (FIFO)
        </li>
      </ul>
    </div>
  )
}
