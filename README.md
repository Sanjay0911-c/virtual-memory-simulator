# Virtual Memory Simulator & Page Replacement Analysis Platform

A web-based Operating Systems project that simulates virtual memory page replacement algorithms, visualizes their behavior step by step, and compares their performance using page faults and hit counts.

Built with **React, Vite, Python, and FastAPI**.

## Features

### 1. Page Replacement Simulation
- Simulate **FIFO (First-In, First-Out)**, **LRU (Least Recently Used)**, and **Optimal** page replacement algorithms.
- Enter a custom page reference string.
- Configure the number of available frames.
- View page hits, page faults, and replaced pages for each reference.
- Inspect the final frame state and performance summary.

### 2. Algorithm Comparison
- Compare FIFO, LRU, and Optimal using the same reference string and frame count.
- View page faults, page hits, and hit/fault statistics side by side.
- Understand how different replacement strategies affect performance.

### 3. Interactive Step Player
- Navigate through simulation steps using Previous and Next controls.
- Play through the simulation to observe how frames change over time.
- Follow page hits, page faults, and page replacements as they occur.

### 4. Frame-Count Analysis
- Analyze how changing the number of frames affects page-fault counts.
- Compare FIFO, LRU, and Optimal across a range of frame counts.
- View results in both a data table and an **SVG graph** plotting page faults against frame count.

### 5. Belady's Anomaly Detection
- Detect and highlight **Belady's anomaly**, where increasing the number of frames can increase page faults.
- Examine the affected frame-count transition in the analysis results.
- Explore why FIFO can exhibit this behavior, while stack algorithms such as LRU and Optimal do not under standard assumptions.

### 6. Workload Generator
Generate page reference strings without entering every value manually.

Supported workload patterns:
- **Sequential:** cycles through page numbers in order.
- **Random:** generates random page references within the selected range.
- **Repeated:** cycles through a fixed pattern of distinct pages.
- **Locality-based:** generates references concentrated around a smaller working set.

Configure the workload length, page range, and supported pattern parameters. Optional seeds allow reproducible random workloads. Generated strings can be used with the existing simulation, comparison, and frame-analysis features.

Generation does not automatically start a simulation. If the reference-string field already contains data, the interface asks before replacing it.

### 7. Replacement Decision Explanations
Enable optional explanations during an individual simulation to understand why a page was selected for replacement.

- **FIFO:** shows the queue order and the page selected for eviction.
- **LRU:** shows last-used information for resident pages.
- **Optimal:** shows the next-use information for candidate pages and explains tie-breaking when applicable.

Explanations are opt-in. The default simulation response remains compatible with the existing response format.

## Algorithms

| Algorithm | Replacement strategy |
|---|---|
| FIFO | Replaces the page that has been in memory the longest. |
| LRU | Replaces the page that has not been used for the longest time. |
| Optimal | Replaces the page whose next use is farthest in the future, or which will not be used again. |

Optimal is included as a theoretical benchmark because it uses future references that a real operating system cannot generally know in advance.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Pydantic |
| Visualization | Inline SVG |
| Testing | Pytest, frontend production build checks |

## Architecture

```text
React Frontend (Vite)
        |
        | /api requests
        v
FastAPI Backend
        |
        +-- Input validation
        |
        +-- Simulation service
        |      +-- FIFO
        |      +-- LRU
        |      +-- Optimal
        |
        +-- Algorithm comparison
        |
        +-- Frame-count analysis
        |
        +-- Workload generation
```

The application uses a stateless backend and does not require a database or user authentication.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/simulate` | Run a page replacement simulation. |
| POST | `/api/compare` | Compare supported algorithms. |
| POST | `/api/frame-analysis` | Analyze page faults across frame counts and detect anomalies. |
| POST | `/api/workload` | Generate page reference strings using a selected workload pattern. |

The simulation endpoint supports an optional `explain` flag to include replacement decision details.

Successful API responses use a standard envelope:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

Error responses include a structured error code and message.

## Getting Started

### Prerequisites

- Python 3.10 or a compatible version supported by the project's dependencies
- Node.js and npm

### 1. Clone the repository

```bash
git clone https://github.com/Sanjay0911-c/virtual-memory-simulator.git
cd virtual-memory-simulator
```

### 2. Set up the backend

From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows — PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows — Command Prompt:**

```bat
.venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

The API should be available at `http://127.0.0.1:8000`. If enabled by the application, interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Set up the frontend

Open another terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite development URL, normally `http://localhost:5173`.

The frontend development server proxies `/api` requests to the FastAPI backend.

## Example

Consider the reference string:

```text
7, 0, 1, 2, 0, 3, 0, 4, 2, 3
```

With **3 frames**, the expected page-fault totals are:

| Algorithm | Page faults | Page hits |
|---|---:|---:|
| FIFO | 9 | 1 |
| LRU | 8 | 2 |
| Optimal | 6 | 4 |

Optimal produces the fewest faults for this reference string, while FIFO and LRU demonstrate how different replacement policies affect memory performance.

## Testing

Run the backend tests from the `backend` directory:

```bash
python -m pytest -q
```

The latest reported backend test run passed **122 tests**. Run the tests again after making changes to confirm the current result.

Build the frontend from the `frontend` directory:

```bash
npm run build
```

## Project Structure

```text
virtual-memory-simulator/
├── backend/
│   ├── app/
│   │   ├── algorithms/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       ├── services/
│       ├── App.jsx
│       └── index.css
├── README.md
└── .gitignore
```

## Learning Objectives

This project demonstrates:
- Virtual memory and demand paging concepts.
- Page hits, page faults, and frame allocation.
- FIFO, LRU, and Optimal page replacement strategies.
- Algorithm performance comparison.
- Belady's anomaly and frame-count analysis.
- Backend API development and frontend-backend integration.
- Interactive visualization and automated testing.

## Future Enhancements

- Add additional page replacement algorithms, such as Clock.
- Explore larger and more varied workloads.
- Improve accessibility and export analysis results.
- Add optional educational walkthroughs for individual simulation steps.

## Contributors

Developed as an Operating Systems project by **Sanjay0911-c**.

## License

No license has been specified yet. Add a `LICENSE` file if you intend to publish the project under an open-source license.
