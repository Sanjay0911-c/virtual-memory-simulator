import { useState } from 'react'
import { generateWorkload } from '../services/api.js'

const TYPES = [
  { value: 'sequential', label: 'Sequential', hint: 'Pages 0, 1, 2, … wrapping around the page range.' },
  { value: 'random', label: 'Random', hint: 'Each reference is chosen uniformly from the page range.' },
  { value: 'repeated', label: 'Repeated', hint: 'A fixed pattern of distinct pages, repeated.' },
  { value: 'locality', label: 'Locality-based', hint: 'Mostly re-uses a small working set that shifts over time.' },
]

/**
 * Generates a reference string via POST /api/workload and hands it to the
 * parent, which puts it in the normal reference-string input. It never runs
 * a simulation, and manual typing in that input is unaffected. If the input
 * already has content, the user must confirm before it is replaced.
 *
 * Optional numeric fields left blank are simply omitted so the backend
 * applies its own defaults; the backend remains the source of truth for
 * validation (this component only does a light "is it a whole number" check).
 */
export default function WorkloadGenerator({ referenceInput, onGenerated, disabled }) {
  const [type, setType] = useState('random')
  const [length, setLength] = useState('20')
  const [pageRange, setPageRange] = useState('8')
  const [seed, setSeed] = useState('')
  const [patternLength, setPatternLength] = useState('')
  const [workingSetSize, setWorkingSetSize] = useState('')
  const [localityProbability, setLocalityProbability] = useState('')

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [info, setInfo] = useState(null)

  const typeInfo = TYPES.find((t) => t.value === type)
  const usesSeed = type !== 'sequential'

  function wholeNumber(raw, label, { required = false, min = 0 } = {}) {
    const text = String(raw).trim()
    if (!text) {
      return required ? { error: `${label} is required.` } : { value: undefined }
    }
    const n = Number(text)
    if (!Number.isInteger(n) || n < min) {
      return { error: `${label} must be a whole number${min > 0 ? ` of at least ${min}` : ' (0 or more)'}.` }
    }
    return { value: n }
  }

  function buildRequest() {
    const body = { type }

    const len = wholeNumber(length, 'Length', { required: true, min: 1 })
    if (len.error) return { error: len.error }
    body.length = len.value

    const range = wholeNumber(pageRange, 'Page range', { required: true, min: 1 })
    if (range.error) return { error: range.error }
    body.page_range = range.value

    if (usesSeed) {
      const s = wholeNumber(seed, 'Seed')
      if (s.error) return { error: s.error }
      if (s.value !== undefined) body.seed = s.value
    }

    if (type === 'repeated') {
      const p = wholeNumber(patternLength, 'Pattern length', { min: 1 })
      if (p.error) return { error: p.error }
      if (p.value !== undefined) body.pattern_length = p.value
    }

    if (type === 'locality') {
      const w = wholeNumber(workingSetSize, 'Working set size', { min: 1 })
      if (w.error) return { error: w.error }
      if (w.value !== undefined) body.working_set_size = w.value

      const probText = localityProbability.trim()
      if (probText) {
        const prob = Number(probText)
        if (!Number.isFinite(prob) || prob < 0 || prob > 1) {
          return { error: 'Locality probability must be a number between 0 and 1.' }
        }
        body.locality_probability = prob
      }
    }

    return { body }
  }

  async function runGeneration() {
    setConfirming(false)
    setError(null)
    setInfo(null)

    const { body, error: validationError } = buildRequest()
    if (validationError) {
      setError(validationError)
      return
    }

    setBusy(true)
    try {
      const data = await generateWorkload(body)
      onGenerated(data.pages.join(', '))
      setInfo(
        `Generated ${data.pages.length} references (${typeInfo.label.toLowerCase()}).` +
          (data.seed !== null ? ` Seed used: ${data.seed} — enter it in the Seed field to reproduce this string.` : '') +
          ' Click Simulate, Compare or Analyze to use it.',
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function handleGenerate() {
    if (referenceInput.trim()) {
      // Don't silently overwrite what the user typed — ask first.
      setError(null)
      setInfo(null)
      setConfirming(true)
    } else {
      runGeneration()
    }
  }

  const isDisabled = disabled || busy

  return (
    <section className="panel" data-testid="workload-generator">
      <h2>Workload Generator</h2>
      <p className="hint">
        Optional. Generate a reference string instead of typing one; it fills the Page Reference
        String box above and does not run a simulation.
      </p>

      <div className="field-row">
        <div className="field">
          <label htmlFor="workload-type">Pattern</label>
          <select
            id="workload-type"
            value={type}
            onChange={(e) => {
              setType(e.target.value)
              setConfirming(false)
            }}
          >
            {TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
          <p className="hint">{typeInfo.hint}</p>
        </div>

        <div className="field">
          <label htmlFor="workload-length">Length</label>
          <input
            id="workload-length"
            type="number"
            min="1"
            max="1000"
            value={length}
            onChange={(e) => setLength(e.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="workload-range">Page range (0 to N−1)</label>
          <input
            id="workload-range"
            type="number"
            min="1"
            value={pageRange}
            onChange={(e) => setPageRange(e.target.value)}
          />
        </div>
      </div>

      {(usesSeed || type === 'repeated' || type === 'locality') && (
        <div className="field-row">
          {type === 'repeated' && (
            <div className="field">
              <label htmlFor="workload-pattern">Pattern length (optional)</label>
              <input
                id="workload-pattern"
                type="number"
                min="1"
                placeholder="default 4"
                value={patternLength}
                onChange={(e) => setPatternLength(e.target.value)}
              />
            </div>
          )}

          {type === 'locality' && (
            <>
              <div className="field">
                <label htmlFor="workload-ws">Working set size (optional)</label>
                <input
                  id="workload-ws"
                  type="number"
                  min="1"
                  placeholder="default 4"
                  value={workingSetSize}
                  onChange={(e) => setWorkingSetSize(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="workload-prob">Locality probability 0–1 (optional)</label>
                <input
                  id="workload-prob"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  placeholder="default 0.8"
                  value={localityProbability}
                  onChange={(e) => setLocalityProbability(e.target.value)}
                />
              </div>
            </>
          )}

          {usesSeed && (
            <div className="field">
              <label htmlFor="workload-seed">Seed (optional)</label>
              <input
                id="workload-seed"
                type="number"
                min="0"
                placeholder="blank = new each time"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
              />
            </div>
          )}
        </div>
      )}

      {confirming && (
        <div className="status status-warning" role="alertdialog" aria-label="Confirm replace" data-testid="workload-confirm">
          <p>The Page Reference String box already has content. Replace it with a generated one?</p>
          <div className="button-row">
            <button className="btn btn-primary" onClick={runGeneration} data-testid="workload-confirm-replace">
              Replace
            </button>
            <button className="btn btn-ghost" onClick={() => setConfirming(false)} data-testid="workload-confirm-cancel">
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="status status-error" data-testid="workload-error">
          ⚠ {error}
        </div>
      )}

      {info && (
        <div className="status status-success" data-testid="workload-info">
          {info}
        </div>
      )}

      {!confirming && (
        <div className="button-row">
          <button className="btn btn-secondary" onClick={handleGenerate} disabled={isDisabled} data-testid="workload-generate">
            {busy ? 'Generating…' : 'Generate Reference String'}
          </button>
        </div>
      )}
    </section>
  )
}
