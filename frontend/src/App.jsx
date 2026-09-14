import { useEffect, useState } from 'react'
import InputPanel from './components/InputPanel.jsx'
import SummaryCards from './components/SummaryCards.jsx'
import StepPlayer from './components/StepPlayer.jsx'
import SimulationTable from './components/SimulationTable.jsx'
import CompareSection from './components/CompareSection.jsx'
import FrameAnalysisPanel from './components/FrameAnalysisPanel.jsx'
import FrameAnalysisResults from './components/FrameAnalysisResults.jsx'
import { simulate, compare, analyzeFrames } from './services/api.js'
import { parseReferenceString } from './services/parseInput.js'

const DEFAULT_ALGORITHM = 'FIFO'
const PLAYBACK_INTERVAL_MS = 900

export default function App() {
  const [referenceInput, setReferenceInput] = useState('')
  const [framesInput, setFramesInput] = useState('')
  const [algorithm, setAlgorithm] = useState(DEFAULT_ALGORITHM)

  const [result, setResult] = useState(null)
  const [compareResult, setCompareResult] = useState(null)

  // Stage 7: frame-count analysis. Reuses the same referenceInput above;
  // only the frame range is new state.
  const [minFramesInput, setMinFramesInput] = useState('')
  const [maxFramesInput, setMaxFramesInput] = useState('')
  const [frameAnalysis, setFrameAnalysis] = useState(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Step-player state: purely an index into result.steps (the trace the
  // backend already computed). No page-replacement logic lives here.
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  // Auto-advance one step every PLAYBACK_INTERVAL_MS while playing. Stops
  // itself at the last step, and is cleaned up whenever playback pauses,
  // the step changes, or the result is replaced (new simulate/compare run).
  useEffect(() => {
    if (!isPlaying || !result) return undefined

    const totalSteps = result.steps.length
    if (currentStepIndex >= totalSteps - 1) {
      setIsPlaying(false)
      return undefined
    }

    const timer = setTimeout(() => {
      setCurrentStepIndex((i) => Math.min(i + 1, totalSteps - 1))
    }, PLAYBACK_INTERVAL_MS)

    return () => clearTimeout(timer)
  }, [isPlaying, currentStepIndex, result])

  // Client-side parse/validate first (fast, friendly). The backend still
  // re-validates everything it receives and remains the source of truth.
  function parseAndValidate() {
    const { pages, error: parseError } = parseReferenceString(referenceInput)
    if (parseError) {
      setError(parseError)
      return null
    }

    const frames = Number(framesInput)
    if (!framesInput.trim() || !Number.isInteger(frames) || frames <= 0) {
      setError('Number of frames must be a positive whole number.')
      return null
    }

    return { pages, frames }
  }

  async function handleSimulate() {
    setError(null)
    const parsed = parseAndValidate()
    if (!parsed) return

    setLoading(true)
    setCompareResult(null)
    setFrameAnalysis(null)
    try {
      const data = await simulate(parsed.pages, parsed.frames, algorithm)
      setResult(data)
      setCurrentStepIndex(0)
      setIsPlaying(false)
    } catch (err) {
      setError(err.message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleCompare() {
    setError(null)
    const parsed = parseAndValidate()
    if (!parsed) return

    setLoading(true)
    setResult(null)
    setFrameAnalysis(null)
    setIsPlaying(false)
    try {
      const data = await compare(parsed.pages, parsed.frames)
      setCompareResult(data)
    } catch (err) {
      setError(err.message)
      setCompareResult(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleAnalyzeFrames() {
    setError(null)

    const { pages, error: parseError } = parseReferenceString(referenceInput)
    if (parseError) {
      setError(parseError)
      return
    }

    const minFrames = Number(minFramesInput)
    if (!minFramesInput.trim() || !Number.isInteger(minFrames) || minFrames <= 0) {
      setError('Min frames must be a positive whole number.')
      return
    }

    const maxFrames = Number(maxFramesInput)
    if (!maxFramesInput.trim() || !Number.isInteger(maxFrames) || maxFrames <= 0) {
      setError('Max frames must be a positive whole number.')
      return
    }

    if (minFrames > maxFrames) {
      setError('Min frames cannot be greater than max frames.')
      return
    }

    setLoading(true)
    setResult(null)
    setCompareResult(null)
    setIsPlaying(false)
    try {
      const data = await analyzeFrames(pages, minFrames, maxFrames)
      setFrameAnalysis(data)
    } catch (err) {
      setError(err.message)
      setFrameAnalysis(null)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setReferenceInput('')
    setFramesInput('')
    setAlgorithm(DEFAULT_ALGORITHM)
    setResult(null)
    setCompareResult(null)
    setError(null)
    setLoading(false)
    setCurrentStepIndex(0)
    setIsPlaying(false)
    setMinFramesInput('')
    setMaxFramesInput('')
    setFrameAnalysis(null)
  }

  // ---- Step-player handlers: index navigation only, no algorithm logic ----

  function handlePreviousStep() {
    setIsPlaying(false)
    setCurrentStepIndex((i) => Math.max(0, i - 1))
  }

  function handleNextStep() {
    setIsPlaying(false)
    setCurrentStepIndex((i) => (result ? Math.min(result.steps.length - 1, i + 1) : i))
  }

  function handlePlay() {
    if (!result) return
    if (currentStepIndex >= result.steps.length - 1) {
      setCurrentStepIndex(0) // replay from the start if already at the end
    }
    setIsPlaying(true)
  }

  function handlePauseStep() {
    setIsPlaying(false)
  }

  function handleResetStep() {
    setIsPlaying(false)
    setCurrentStepIndex(0)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Virtual Memory Simulator</h1>
        <p>Page Replacement Analysis Platform</p>
      </header>

      <main className="app-main">
        <InputPanel
          referenceInput={referenceInput}
          onReferenceChange={setReferenceInput}
          framesInput={framesInput}
          onFramesChange={setFramesInput}
          algorithm={algorithm}
          onAlgorithmChange={setAlgorithm}
          onSimulate={handleSimulate}
          onCompare={handleCompare}
          onReset={handleReset}
          loading={loading}
        />

        {loading && (
          <div className="status status-loading" data-testid="status-loading">
            Running simulation…
          </div>
        )}

        {error && (
          <div className="status status-error" data-testid="status-error">
            ⚠ {error}
          </div>
        )}

        <SummaryCards result={result} />
        <StepPlayer
          result={result}
          currentStepIndex={currentStepIndex}
          isPlaying={isPlaying}
          onPrevious={handlePreviousStep}
          onNext={handleNextStep}
          onPlay={handlePlay}
          onPause={handlePauseStep}
          onResetStep={handleResetStep}
        />
        <SimulationTable result={result} />
        <CompareSection compareResult={compareResult} />

        <FrameAnalysisPanel
          minFramesInput={minFramesInput}
          onMinFramesChange={setMinFramesInput}
          maxFramesInput={maxFramesInput}
          onMaxFramesChange={setMaxFramesInput}
          onAnalyze={handleAnalyzeFrames}
          loading={loading}
        />
        <FrameAnalysisResults analysis={frameAnalysis} />
      </main>
    </div>
  )
}
