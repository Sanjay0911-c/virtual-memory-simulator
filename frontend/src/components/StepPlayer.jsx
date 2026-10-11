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

      <StepExplanation step={current} />

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

/**
 * Shows WHY the current step happened. For an eviction it displays the
 * backend's own `decision` block (victim, per-page evidence, reason text) —
 * nothing is recomputed here. Hits and placements into an empty frame have
 * no victim, so they get a fixed message based on fields already in the step.
 */
function StepExplanation({ step }) {
  if (step.result === 'HIT') {
    return (
      <div className="decision-box decision-neutral" data-testid="step-explanation">
        <strong>No replacement.</strong> Page {step.page} is already in memory, so this is a hit and
        no victim was chosen.
      </div>
    )
  }

  if (step.replaced_page === null) {
    return (
      <div className="decision-box decision-neutral" data-testid="step-explanation">
        <strong>No replacement.</strong> Page {step.page} faulted, but a frame was still empty, so
        it was loaded there and no victim was chosen.
      </div>
    )
  }

  const decision = step.decision
  if (!decision) {
    return (
      <div className="decision-box decision-neutral" data-testid="step-explanation">
        Page {step.replaced_page} was replaced. No decision details were provided for this run.
      </div>
    )
  }

  const evidenceHeader =
    decision.policy === 'FIFO'
      ? 'Loaded at step'
      : decision.policy === 'LRU'
        ? 'Last used at step'
        : 'Next used at step'

  function evidenceValue(candidate) {
    if (decision.policy === 'FIFO') return candidate.loaded_at
    if (decision.policy === 'LRU') return candidate.last_used
    return candidate.next_use === null ? 'never again' : candidate.next_use
  }

  return (
    <div className="decision-box" data-testid="step-explanation">
      <div className="decision-title">
        Why page <strong>{decision.victim}</strong> was replaced
        {decision.tie_broken && <span className="badge badge-fault"> tie broken by frame order</span>}
      </div>
      <p className="decision-reason" data-testid="decision-reason">
        {decision.reason}
      </p>
      <div className="table-scroll">
        <table className="sim-table decision-table">
          <thead>
            <tr>
              <th>Resident page</th>
              <th>{evidenceHeader}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {decision.candidates.map((c) => (
              <tr key={c.page} className={c.page === decision.victim ? 'row-fault' : undefined}>
                <td>{c.page}</td>
                <td>{evidenceValue(c)}</td>
                <td>{c.page === decision.victim ? 'Victim' : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
