/**
 * Thin wrapper around the two backend endpoints. This is the ONLY file
 * in the frontend that calls fetch() — every component goes through
 * simulate()/compare() instead of talking to the network directly.
 *
 * Both functions return `data` from a successful {success, data, error}
 * envelope, or throw an Error whose .message is ready to show the user
 * and whose .code carries the backend's error code (e.g.
 * "INVALID_FRAME_COUNT") for anything that needs it.
 */

const BASE_URL = '/api'

async function postJSON(path, body) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch (networkError) {
    throw new Error('Could not reach the backend. Is the FastAPI server running?')
  }

  let payload
  try {
    payload = await response.json()
  } catch (parseError) {
    throw new Error('The server returned an unexpected (non-JSON) response.')
  }

  if (!payload.success) {
    const message = payload.error?.message || 'The request failed.'
    const error = new Error(message)
    error.code = payload.error?.code || 'UNKNOWN_ERROR'
    throw error
  }

  return payload.data
}

export function simulate(pages, frames, algorithm) {
  return postJSON('/simulate', { pages, frames, algorithm })
}

export function compare(pages, frames) {
  return postJSON('/compare', { pages, frames })
}

export function analyzeFrames(pages, minFrames, maxFrames) {
  return postJSON('/frame-analysis', { pages, min_frames: minFrames, max_frames: maxFrames })
}
