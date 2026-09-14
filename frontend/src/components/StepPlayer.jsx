/**
 * Step-by-step playback of an already-computed simulation.
 *
 * IMPORTANT: this component does NOT run any page replacement logic.
 * It only reads `result.steps[currentStepIndex]` — the exact trace the
 * backend already returned from /api/simulate — and walks an index
 * back and forth over it. FIFO/LRU/Optimal stay backend-only; this is
 * purely a "scrub through data we already have" UI, per the Stage 6
 * requirement to stay synchronized with the existing simulation data
 * instead of re-implementing an algorithm in the frontend.
 */
export default function StepPlayer({
  result,
  currentStepIndex,
  isPlaying,
  onPrevious,
  onNext,
  onPlay,
  onPause,
  onResetStep,
}) {
  if (!result) return null

  const steps = result.steps
  const totalSteps = steps.length
  const current = steps[currentStepIndex]

  const atStart = currentStepIndex === 0
  const atEnd = currentStepIndex === totalSteps - 1

  return (
    <section className="panel" data-testid="step-player">
      <h2>Step-by-Step Playback — {result.algorithm}</h2>

      <div className="step-status-row">
        <span className="step-counter" data-testid="step-counter">
          Step {current.step} of {totalSteps}
        </span>
        <span className="step-page">
          Requesting Page: <strong>{current.page}</strong>
        </span>
        <span
          className={`badge ${current.result === 'FAULT' ? 'badge-fault' : 'badge-hit'}`}
          data-testid="step-result-badge"
        >
          {current.result === 'FAULT' ? 'PAGE FAULT' : 'HIT'}
        </span>
        {current.replaced_page !== null && (
          <span className="step-replaced" data-testid="step-replaced">
            Replaced Page: <strong>{current.replaced_page}</strong>
          </span>
        )}
      </div>

      <div className="frame-visual" data-testid="frame-visual">
        {current.frames.map((value, idx) => {
          const isActiveSlot = value === current.page
          let slotClass = 'frame-box'
          if (value === null) {
            slotClass += ' frame-empty'
          } else if (isActiveSlot && current.result === 'FAULT') {
            slotClass += ' frame-fault'
          } else if (isActiveSlot && current.result === 'HIT') {
            slotClass += ' frame-hit'
          }

          return (
            <div className={slotClass} key={idx} data-testid={`frame-slot-${idx}`}>
              <div className="frame-slot-label">Frame {idx + 1}</div>
              <div className="frame-slot-value">{value === null ? '—' : value}</div>
            </div>
          )
        })}
      </div>

      <div className="button-row">
        <button
          className="btn btn-ghost"
          onClick={onPrevious}
          disabled={atStart}
          data-testid="step-prev"
        >
          ⏮ Previous
        </button>
        {isPlaying ? (
          <button className="btn btn-secondary" onClick={onPause} data-testid="step-pause">
            ⏸ Pause
          </button>
        ) : (
          <button
            className="btn btn-secondary"
            onClick={onPlay}
            disabled={totalSteps <= 1}
            data-testid="step-play"
          >
            ▶ Play
          </button>
        )}
        <button className="btn btn-ghost" onClick={onNext} disabled={atEnd} data-testid="step-next">
          Next ⏭
        </button>
        <button className="btn btn-ghost" onClick={onResetStep} data-testid="step-reset">
          ↺ Reset
        </button>
      </div>
    </section>
  )
}
