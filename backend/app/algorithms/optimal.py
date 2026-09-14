"""
Optimal (MIN / Belady's) Page Replacement Algorithm.

OS concept: the theoretical best-case replacement policy — on a fault,
evict whichever resident page's NEXT use lies farthest in the future
(or is never used again). No real operating system can implement this
online, since it requires knowing future memory accesses in advance.
It exists purely as a benchmark: it shows the fewest page faults any
algorithm could possibly achieve on a given reference string, so
FIFO/LRU results can be measured against it.

Pure function, same contract as fifo.simulate_fifo / lru.simulate_lru.
Requires the full reference string up front — this is a batch/offline
simulation, not a live/streaming one, which is exactly what makes
"looking into the future" possible here but not in a real kernel.
"""

from typing import List, Optional

from app.algorithms.types import Step


def simulate_optimal(pages: List[int], frame_count: int) -> List[Step]:
    """Run Optimal page replacement over `pages` with `frame_count` frames.

    Frame slots are stable positions, same convention as FIFO/LRU.
    Ties (two resident pages both never used again) are broken
    deterministically by slot order (the page occupying the lowest
    slot index is evicted first).

    Raises:
        ValueError: if frame_count is not a positive integer.
    """
    if frame_count <= 0:
        raise ValueError("frame_count must be greater than zero")

    frame_slots: List[Optional[int]] = [None] * frame_count
    steps: List[Step] = []

    for i, page in enumerate(pages):
        step_num = i + 1
        replaced_page: Optional[int] = None

        if page in frame_slots:
            result = "HIT"
        else:
            result = "FAULT"
            if None in frame_slots:
                slot = frame_slots.index(None)
                frame_slots[slot] = page
            else:
                future = pages[i + 1 :]

                def next_use_distance(candidate: int) -> float:
                    return future.index(candidate) if candidate in future else float("inf")

                victim_page = max(
                    (p for p in frame_slots if p is not None),
                    key=next_use_distance,
                )
                slot = frame_slots.index(victim_page)
                replaced_page = victim_page
                frame_slots[slot] = page

        steps.append(
            {
                "step": step_num,
                "page": page,
                "frames": frame_slots.copy(),
                "result": result,
                "replaced_page": replaced_page,
            }
        )

    return steps
