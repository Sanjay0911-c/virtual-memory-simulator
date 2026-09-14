/**
 * Client-side parsing/normalization of the reference-string field, per
 * the project spec: accept "7,0,1", "7 0 1", and "7, 0, 1" all as the
 * same input. This is a fast, friendly first check — the backend still
 * re-validates everything and remains the source of truth (e.g. it
 * rejects a reference string that's absurdly long, which this function
 * doesn't need to know about).
 */
export function parseReferenceString(raw) {
  const trimmed = (raw ?? '').trim()

  if (!trimmed) {
    return { pages: null, error: 'Enter a page reference string, e.g. 7,0,1,2,0,3' }
  }

  const tokens = trimmed.split(/[\s,]+/).filter(Boolean)
  const pages = []

  for (const token of tokens) {
    if (!/^\d+$/.test(token)) {
      return {
        pages: null,
        error: `"${token}" is not a valid page number — use non-negative integers only.`,
      }
    }
    pages.push(Number(token))
  }

  return { pages, error: null }
}
