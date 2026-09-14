"""
Simulation service — the orchestration layer between the API and the
algorithm modules.

This is deliberately the ONLY place that:
  - knows about all three algorithms at once,
  - decides which one to call for a given request,
  - turns a raw step trace into the metrics (hit ratio, fault ratio,
    replacements) the frontend displays.

The algorithm modules themselves (app/algorithms/*.py) are untouched —
they still just take (pages, frame_count) and return a step trace, with
no idea this service or FastAPI exist.
"""

from typing import Dict, List

from app.algorithms.fifo import simulate_fifo
from app.algorithms.lru import simulate_lru
from app.algorithms.optimal import simulate_optimal
from app.services.validation import (
    validate_algorithm,
    validate_frame_range,
    validate_frames,
    validate_pages,
)

ALGORITHM_FUNCS = {
    "FIFO": simulate_fifo,
    "LRU": simulate_lru,
    "OPTIMAL": simulate_optimal,
}


def run_simulation(pages: List[int], frames: int, algorithm: str) -> Dict:
    """Validate input, run ONE algorithm, and return its full result block."""
    validate_pages(pages)
    validate_frames(frames)
    algo_name = validate_algorithm(algorithm)

    steps = ALGORITHM_FUNCS[algo_name](pages, frames)
    return _build_result(algo_name, steps)


def run_comparison(pages: List[int], frames: int) -> Dict:
    """Validate input once, run ALL THREE algorithms on the same input."""
    validate_pages(pages)
    validate_frames(frames)

    results = {
        algo_name: _build_result(algo_name, func(pages, frames))
        for algo_name, func in ALGORITHM_FUNCS.items()
    }

    return {
        "reference_string": pages,
        "frames": frames,
        "results": results,
    }


def run_frame_analysis(pages: List[int], min_frames: int, max_frames: int) -> Dict:
    """Frame-count analysis (Stage 7): run all three algorithms across every
    frame count from min_frames to max_frames (inclusive) on the SAME
    reference string, so the caller can see how fault counts change as
    memory grows — and detect Belady's anomaly in the FIFO series.

    This does not add a fourth algorithm or any new replacement logic: it
    calls the exact same ALGORITHM_FUNCS used by run_simulation/
    run_comparison, once per frame count, and reuses _build_result for the
    metrics. The only new logic here is the sweep loop and the anomaly
    check over FIFO's fault counts.
    """
    validate_pages(pages)
    validate_frame_range(min_frames, max_frames)

    sweep = []
    fifo_fault_series = []  # [(frame_count, fifo_page_faults), ...] for Belady's check

    for frame_count in range(min_frames, max_frames + 1):
        per_algorithm = {
            algo_name: _build_summary(algo_name, func(pages, frame_count))
            for algo_name, func in ALGORITHM_FUNCS.items()
        }
        sweep.append({"frames": frame_count, "results": per_algorithm})
        fifo_fault_series.append((frame_count, per_algorithm["FIFO"]["page_faults"]))

    occurrences = _detect_belady_anomaly(fifo_fault_series)

    return {
        "reference_string": pages,
        "min_frames": min_frames,
        "max_frames": max_frames,
        "sweep": sweep,
        "belady_anomaly": {
            "detected": len(occurrences) > 0,
            "occurrences": occurrences,
            "explanation": (
                "Belady's anomaly occurs when increasing the number of available "
                "page frames leads to MORE page faults instead of fewer. It is "
                "specific to FIFO here because FIFO evicts pages purely by "
                "arrival order, with no regard for how recently or frequently a "
                "page is used — LRU and Optimal do not exhibit this anomaly."
            ),
        },
    }


def _detect_belady_anomaly(fifo_fault_series: List[tuple]) -> List[Dict]:
    """fifo_fault_series is [(frame_count, fifo_page_faults), ...] sorted by
    frame_count ascending (the sweep loop above always builds it that way).
    Flags every consecutive pair where faults went UP as frames increased —
    the defining symptom of Belady's anomaly.
    """
    occurrences = []
    for (prev_frames, prev_faults), (curr_frames, curr_faults) in zip(
        fifo_fault_series, fifo_fault_series[1:]
    ):
        if curr_faults > prev_faults:
            occurrences.append(
                {
                    "from_frames": prev_frames,
                    "to_frames": curr_frames,
                    "from_faults": prev_faults,
                    "to_faults": curr_faults,
                }
            )
    return occurrences


def _build_summary(algorithm: str, steps: List[Dict]) -> Dict:
    """Same metrics as _build_result, minus the full step trace. A
    multi-frame-count, multi-algorithm sweep only needs aggregate numbers
    per (algorithm, frame count) — not a full replay trace for each one,
    which would make the response far larger than necessary."""
    summary = _build_result(algorithm, steps)
    del summary["steps"]
    return summary


def _build_result(algorithm: str, steps: List[Dict]) -> Dict:
    """Turn a raw step trace into the summary metrics the API/frontend need.

    hit_ratio / fault_ratio = (hits or faults / total requests) * 100,
    rounded to 2 decimal places, as specified in the project requirements.
    """
    total_requests = len(steps)
    page_faults = sum(1 for s in steps if s["result"] == "FAULT")
    page_hits = total_requests - page_faults
    replacements = sum(1 for s in steps if s["replaced_page"] is not None)

    hit_ratio = round((page_hits / total_requests) * 100, 2) if total_requests else 0.0
    fault_ratio = round((page_faults / total_requests) * 100, 2) if total_requests else 0.0

    return {
        "algorithm": algorithm,
        "total_requests": total_requests,
        "page_faults": page_faults,
        "page_hits": page_hits,
        "hit_ratio": hit_ratio,
        "fault_ratio": fault_ratio,
        "replacements": replacements,
        "steps": steps,
    }
