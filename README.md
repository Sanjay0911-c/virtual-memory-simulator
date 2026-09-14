# Virtual Memory Simulator & Page Replacement Analysis Platform

An educational, full-stack simulator that demonstrates how virtual memory and page replacement work in an operating system. Users supply a page reference string and a number of physical memory frames, choose an algorithm (or compare all three at once), and see a step-by-step trace of hits, faults, and frame contents — computed by real implementations of FIFO, LRU, and Optimal (MIN) page replacement, not hardcoded results.

This is a simulation and analysis tool. It does not read, control, or modify the host computer's actual RAM or operating system memory manager in any way.

## Overview

The platform is a two-part application: a Python/FastAPI backend that implements the three page replacement algorithms and exposes them over a small JSON API, and a React/Vite frontend that collects input, calls that API, and visualizes the results — as a step-by-step animated playback, a full simulation table, a side-by-side algorithm comparison, and a frame-count sweep that can detect Belady's anomaly.

The backend holds no state between requests (no database): every simulation is computed fresh from the request's reference string, frame count, and algorithm choice.

## Problem Statement

Page replacement algorithms are a core Operating Systems topic, but they are usually taught through static diagrams or hand-traced examples on paper. This makes it hard to explore "what if" questions quickly — what happens with a different frame count, how do FIFO and LRU actually diverge on the same input, or when does Belady's anomaly actually occur — without redoing the trace by hand each time. This project addresses that gap with an interactive tool that computes and visualizes these algorithms on demand.

## Objectives

- Correctly implement FIFO, LRU, and Optimal page replacement as independent, testable algorithms.
- Expose them through a clean, validated web API with a consistent response format.
- Visualize a simulation step by step, not just as a final fault count.
- Allow direct, same-input comparison of all three algorithms.
- Demonstrate, computationally, how fault counts change as frame count changes — including Belady's anomaly for FIFO.
- Keep the system's scope appropriate for a course project: no authentication, no database, no unrelated infrastructure.

## Features

- **Virtual memory / page replacement simulation** — enter a page reference string and a frame count and run a full simulation.
- **FIFO** (First-In-First-Out) page replacement.
- **LRU** (Least Recently Used) page replacement.
- **Optimal** (MIN / Belady's) page replacement.
- **Step-by-step playback** — Previous / Next / Play / Pause / Reset controls that scrub through the exact trace the backend computed, with a visual representation of frame contents, the current page request, HIT/PAGE FAULT status, and the replaced page (when applicable).
- **Algorithm comparison** — run FIFO, LRU, and Optimal on the same reference string and frame count in a single request, displayed as a comparison table.
- **Frame-count analysis** — sweep a range of frame counts and see how the fault count for each algorithm changes as memory grows.
- **Belady's anomaly detection** — automatically flags, from the frame-count analysis, any case where increasing FIFO's frame count increases its fault count, with a plain-language explanation.
- **Input validation and error handling** — invalid reference strings, frame counts, algorithm names, and frame ranges are rejected with specific, named error codes rather than crashing or returning inconsistent responses.

## How It Works

1. The user enters a page reference string (e.g. `7,0,1,2,0,3,0,4,2,3`), a number of frames, and selects an algorithm in the React UI.
2. The frontend normalizes the input (accepting comma- or space-separated numbers) and sends it as JSON to the FastAPI backend.
3. FastAPI validates the request, then the simulation service runs the selected algorithm module, which processes the reference string one page at a time, maintaining the current frame contents and recording each step (page requested, frame contents afterward, HIT or FAULT, and the replaced page if any).
4. The simulation service turns that step trace into summary metrics (total requests, faults, hits, hit ratio, fault ratio, replacements) and returns everything as JSON.
5. The React frontend renders the summary cards, the step-by-step playback view, and the full table from that response — no algorithm logic runs in the browser.

## Algorithms

All three algorithms live in the backend as independent, pure functions (`pages`, `frame_count` in → a step-by-step trace out) with no knowledge of the web layer, and each is unit-tested in isolation.

### FIFO — First In, First Out

Tracks pages purely by arrival order. When a page fault occurs and memory is full, FIFO evicts whichever resident page has been in memory the longest, regardless of how recently or frequently it has been used. This simplicity is also what makes FIFO the only one of the three algorithms capable of Belady's anomaly.

### LRU — Least Recently Used

Tracks, for every resident page, the step at which it was last referenced. On a fault with full memory, it evicts the page that has gone unused for the longest time. This exploits temporal locality of reference and generally performs closer to Optimal than FIFO does on realistic access patterns.

### Optimal (MIN)

On a fault with full memory, evicts the resident page whose next use lies farthest in the future (or is never used again). This is implemented as a genuine "look ahead into the rest of the reference string" computation.

**Optimal is included as an educational/theoretical benchmark, not a deployable algorithm.** It requires knowing the entire future reference string in advance, which is only possible here because the whole string is submitted up front for a one-shot simulation. No real operating system can implement Optimal online, since it cannot know future memory accesses; its purpose in this project is to show the fewest page faults any algorithm could achieve on a given input, so FIFO and LRU can be measured against that ceiling.

## Belady's Anomaly

Belady's anomaly is the counterintuitive case where *increasing* the number of available page frames *increases* — rather than decreases — the number of page faults. It is specific to algorithms like FIFO that decide evictions purely by arrival order, with no regard for how recently or frequently a page is used; LRU and Optimal do not exhibit it.

The platform detects this automatically as part of frame-count analysis: it runs FIFO across every frame count in the requested range and checks each consecutive pair of frame counts for an increase in fault count. If one is found, it is reported with the exact frame counts and fault counts involved and a short explanation; if none is found, the platform reports that plainly rather than claiming an anomaly occurred. Belady's anomaly does not occur for every reference string, and the tool never asserts that it does.

## Technology Stack

**Frontend**
- React
- Vite
- JavaScript
- CSS

**Backend**
- Python
- FastAPI
- Pydantic
- pytest

No database, authentication system, or external services are used.

## Architecture

Browser (React UI)
|
API service (fetch wrapper)
|
FastAPI application
|
API routes (/api/simulate, /api/compare, /api/frame-analysis)
|
Pydantic request validation -> semantic validation (validation.py)
|
Simulation service (orchestration + metrics)
|
Algorithm modules (fifo.py / lru.py / optimal.py)


- **Frontend (React):** collects input, calls the API through a single `services/api.js` module, and renders the response — summary cards, step-by-step playback, the full simulation table, the comparison table, and the frame-count analysis view. No page-replacement logic exists in the frontend; every number displayed came from the backend.
- **FastAPI backend:** a thin HTTP layer — each route handler parses an already-validated request and calls the simulation service.
- **Simulation service (`simulation_service.py`):** the only place that knows about all three algorithms at once. It dispatches to the correct algorithm module, runs single simulations, comparisons, or frame-count sweeps, computes summary metrics from a raw step trace, and detects Belady's anomaly from a FIFO fault-count series.
- **Algorithm modules (`algorithms/fifo.py`, `lru.py`, `optimal.py`):** independent, pure functions with no dependency on FastAPI or each other.

## Project Structure

project-root/
backend/
app/
main.py FastAPI app, routers, exception handlers
algorithms/
types.py Shared Step type (data shape only, no logic)
fifo.py
lru.py
optimal.py
api/
simulate.py POST /api/simulate
compare.py POST /api/compare
frame_analysis.py POST /api/frame-analysis
models/
requests.py Pydantic request schemas
envelope.py {success, data, error} response envelope
services/
validation.py Semantic input validation, error codes
simulation_service.py Orchestration, metrics, Belady detection
tests/
test_fifo.py
test_lru.py
test_optimal.py
test_api_simulate.py
test_api_compare.py
test_api_frame_analysis.py
requirements.txt
frontend/
index.html
package.json
vite.config.js
src/
main.jsx
App.jsx
index.css
components/
InputPanel.jsx
SummaryCards.jsx
StepPlayer.jsx
SimulationTable.jsx
CompareSection.jsx
FrameAnalysisPanel.jsx
FrameAnalysisResults.jsx
services/
api.js
parseInput.js
docs/
.gitignore
README.md


## API Overview

Every endpoint returns the same response envelope:

```json
{ "success": true,  "data": { ... }, "error": null }
{ "success": false, "data": null,    "error": { "code": "INVALID_FRAME_COUNT", "message": "Number of frames must be greater than zero" } }
```

Error codes used: `INVALID_INPUT`, `INVALID_ALGORITHM`, `INVALID_FRAME_COUNT`, `INVALID_REFERENCE_STRING`, `INVALID_FRAME_RANGE`, `INTERNAL_ERROR`.

### POST /api/simulate

Runs one algorithm and returns its full step-by-step trace.

Request:
```json
{
  "pages": [7, 0, 1, 2, 0, 3, 0, 4, 2, 3],
  "frames": 3,
  "algorithm": "FIFO"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "algorithm": "FIFO",
    "total_requests": 10,
    "page_faults": 9,
    "page_hits": 1,
    "hit_ratio": 10.0,
    "fault_ratio": 90.0,
    "replacements": 6,
    "steps": [
      { "step": 1, "page": 7, "frames": [7, null, null], "result": "FAULT", "replaced_page": null },
      { "step": 2, "page": 0, "frames": [7, 0, null], "result": "FAULT", "replaced_page": null }
    ]
  },
  "error": null
}
```
(`steps` continues for all 10 requests; truncated above for brevity.)

### POST /api/compare

Runs FIFO, LRU, and Optimal on the same input in one request.

Request:
```json
{
  "pages": [7, 0, 1, 2, 0, 3, 0, 4, 2, 3],
  "frames": 3
}
```

Response (each algorithm's block has the same shape as `/api/simulate`'s `data`):
```json
{
  "success": true,
  "data": {
    "reference_string": [7, 0, 1, 2, 0, 3, 0, 4, 2, 3],
    "frames": 3,
    "results": {
      "FIFO":    { "algorithm": "FIFO",    "page_faults": 9, "page_hits": 1, "hit_ratio": 10.0, "fault_ratio": 90.0, "...": "..." },
      "LRU":     { "algorithm": "LRU",     "page_faults": 8, "page_hits": 2, "hit_ratio": 20.0, "fault_ratio": 80.0, "...": "..." },
      "OPTIMAL": { "algorithm": "OPTIMAL", "page_faults": 6, "page_hits": 4, "hit_ratio": 40.0, "fault_ratio": 60.0, "...": "..." }
    }
  },
  "error": null
}
```

### POST /api/frame-analysis

Runs FIFO, LRU, and Optimal across a range of frame counts on the same reference string, and checks the FIFO series for Belady's anomaly.

Request:
```json
{
  "pages": [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5],
  "min_frames": 1,
  "max_frames": 6
}
```

Response:
```json
{
  "success": true,
  "data": {
    "reference_string": [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5],
    "min_frames": 1,
    "max_frames": 6,
    "sweep": [
      { "frames": 1, "results": { "FIFO": { "page_faults": 12, "...": "..." }, "LRU": { "...": "..." }, "OPTIMAL": { "...": "..." } } },
      { "frames": 3, "results": { "FIFO": { "page_faults": 9,  "...": "..." }, "LRU": { "...": "..." }, "OPTIMAL": { "...": "..." } } },
      { "frames": 4, "results": { "FIFO": { "page_faults": 10, "...": "..." }, "LRU": { "...": "..." }, "OPTIMAL": { "...": "..." } } }
    ],
    "belady_anomaly": {
      "detected": true,
      "occurrences": [
        { "from_frames": 3, "to_frames": 4, "from_faults": 9, "to_faults": 10 }
      ],
      "explanation": "Belady's anomaly occurs when increasing the number of available page frames leads to MORE page faults instead of fewer. It is specific to FIFO here because FIFO evicts pages purely by arrival order, with no regard for how recently or frequently a page is used — LRU and Optimal do not exhibit this anomaly."
    }
  },
  "error": null
}
```
(`sweep` contains one entry per frame count in the requested range; the `results` blocks in each entry omit the per-step trace to keep a multi-frame-count sweep lightweight.)

## Installation and Setup

Requires Python 3.11+ and Node.js 18+.

### Backend setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000` by default. A health check is available at `GET /`.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:5173` by default. Its dev server (see `vite.config.js`) proxies `/api/*` requests to `http://127.0.0.1:8000`, so **the backend must be running** for the frontend to work. No manual API base URL configuration is needed for local development.

### Running both

Start the backend first, then the frontend, in two separate terminals, then open `http://127.0.0.1:5173` in a browser.

## Usage

Example: with the backend and frontend both running, enter the following in the UI:

- **Page reference string:** `7,0,1,2,0,3,0,4,2,3`
- **Number of frames:** `3`

Running **Simulate** with each algorithm, or running **Compare Algorithms** once, produces:

| Algorithm | Page Faults | Page Hits | Hit Ratio | Fault Ratio |
|---|---|---|---|---|
| FIFO    | 9 | 1 | 10% | 90% |
| LRU     | 8 | 2 | 20% | 80% |
| Optimal | 6 | 4 | 40% | 60% |

These figures were hand-traced during development, then verified against the running application (both the API response and the rendered browser UI) before being relied on anywhere else in the project.

For frame-count analysis and Belady's anomaly, the reference string `1,2,3,4,1,2,5,1,2,3,4,5` with a frame range of 1–6 reproduces the classic textbook anomaly: FIFO faults go 12, 12, 9, 10, 5, 5 as frames increase, with the anomaly flagged at the 3→4 frame transition.

## Testing

Backend automated tests (`pytest`, run from `backend/`): **60 tests, all passing** —

- `test_fifo.py`, `test_lru.py`, `test_optimal.py`: 9 tests each, covering normal reference strings, repeated pages, all-unique pages, a single frame, frames greater than unique pages, a reference string shorter than the frame count, empty input, and invalid frame counts, plus one hand-verified known example per algorithm.
- `test_api_simulate.py`: 16 tests covering the response envelope shape, all three algorithms against hand-verified results, case-insensitive algorithm names, the exact step-object shape, and every validation error path (bad frame count, unknown algorithm, empty/negative/oversized reference string, missing fields, wrong types).
- `test_api_compare.py`: 5 tests covering the comparison response shape, hand-verified results across all three algorithms, and its own validation error paths.
- `test_api_frame_analysis.py`: 12 tests covering the sweep response shape, cross-checking sweep results against direct `/api/simulate` calls, a known Belady's anomaly reference string, a case with no anomaly, a degenerate single-frame-count range, and all validation error paths (invalid frame counts, an inverted or overly wide range, empty input, missing fields, wrong types).

Beyond the automated suite, every stage of development was also verified by running the actual backend and frontend together and exercising the real UI in a browser (filling in the classic reference string, stepping through playback, running comparisons and frame-count analysis, and triggering each error case) to confirm the browser matched the API's own numbers. That verification was done with temporary scripts during development and is not included as a committed test suite in this repository — the 60 `pytest` tests listed above are what a fresh clone of this project can run and reproduce directly.

## Future Enhancements

The following were intentionally left out of this project's scope and would be reasonable next steps:

- A chart/graph view of the frame-count analysis sweep, in addition to the current table.
- CSV or JSON export of simulation and comparison results.
- Saving recent simulations in the browser (e.g. via `localStorage`) for quick recall.
- Additional replacement algorithms (e.g. Clock/Second-Chance, LFU) as further points of comparison.
- Deployment configuration for hosting the application outside local development.

## Academic Project Note

This project was built as a 3rd-year Computer Science and Engineering Operating Systems course project. It is a simulation and visualization tool intended to demonstrate understanding of virtual memory, paging, and page replacement algorithms (FIFO, LRU, and Optimal), including Belady's anomaly — it does not modify or interact with any real operating system's memory management.
