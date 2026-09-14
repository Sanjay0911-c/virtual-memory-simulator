"""
LRU (Least Recently Used) Page Replacement Algorithm.

OS concept: approximates an operating system that tracks, for every
resident page, how long ago it was last referenced — and evicts the
page that has gone unused for the LONGEST time. This exploits temporal
locality of reference (pages used recently tend to be used again soon),
which is why LRU usually performs closer to the Optimal algorithm than
FIFO does on realistic access patterns.

Pure function, same contract as fifo.simulate_fifo: reference string +
frame count in, step-by-step trace out. No FastAPI/HTTP knowledge here.
"""

from typing import List, Optional

from app.algorithms.types import Step


def simulate_lru(pages: List[int], frame_count: int) -> List[Step]:
    """Run LRU page replacement over `pages` with `frame_count` frames.

    Frame slots are stable positions, same convention as FIFO: a newly
    loaded page takes the slot of the page it replaced.

    Raises:
        ValueError: if frame_count is not a positive integer.
    """
    if frame_count <= 0:
        raise ValueError("frame_count must be greater than zero")

    frame_slots: List[Optional[int]] = [None] * frame_count
    last_used: dict = {}  # page -> step index it was most recently referenced at
    steps: List[Step] = []

    for i, page in enumerate(pages, start=1):
        replaced_page: Optional[int] = None

        if page in frame_slots:
            result = "HIT"
        else:
            result = "FAULT"
            if None in frame_slots:
                slot = frame_slots.index(None)
                frame_slots[slot] = page
            else:
                # Victim = resident page with the smallest (oldest) last-used step.
                victim_page = min(
                    (p for p in frame_slots if p is not None),
                    key=lambda p: last_used[p],
                )
                slot = frame_slots.index(victim_page)
                replaced_page = victim_page
                frame_slots[slot] = page
                del last_used[victim_page]

        last_used[page] = i

        steps.append(
            {
                "step": i,
                "page": page,
                "frames": frame_slots.copy(),
                "result": result,
                "replaced_page": replaced_page,
            }
        )

    return steps
