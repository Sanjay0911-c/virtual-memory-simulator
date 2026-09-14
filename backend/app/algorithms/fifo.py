"""
FIFO (First-In-First-Out) Page Replacement Algorithm.

OS concept: models an operating system that only tracks *arrival order*
of pages in physical memory. When a new page must be loaded and no free
frame is available, the OS evicts whichever resident page has been in
memory the LONGEST — regardless of how recently or how often it has
been used since. This simplicity is exactly what makes FIFO capable of
Belady's anomaly (adding MORE frames can sometimes cause MORE faults),
since eviction order depends only on arrival, not on usage.

This module is a pure function: it knows nothing about FastAPI, HTTP,
or the web layer. Given a reference string and a frame count, it
returns the full step-by-step simulation trace. The API layer and
simulation service (added in a later stage) are responsible for
turning this trace into an HTTP response.
"""

from collections import deque
from typing import List, Optional

from app.algorithms.types import Step


def simulate_fifo(pages: List[int], frame_count: int) -> List[Step]:
    """Run FIFO page replacement over `pages` with `frame_count` frames.

    Returns a list of per-step records: one dict per page reference,
    each showing the frame contents *after* processing that reference.

    Frame "slots" are stable positions (like Frame 1 / Frame 2 / Frame 3
    columns in a textbook table): a newly loaded page takes the slot of
    whichever page it replaced, so the visualization can show a page
    consistently occupying "its" column until it is evicted.

    Raises:
        ValueError: if frame_count is not a positive integer.
    """
    if frame_count <= 0:
        raise ValueError("frame_count must be greater than zero")

    frame_slots: List[Optional[int]] = [None] * frame_count
    fifo_queue: deque = deque()  # slot indices, oldest-filled first
    steps: List[Step] = []

    for i, page in enumerate(pages, start=1):
        replaced_page: Optional[int] = None

        if page in frame_slots:
            result = "HIT"
        else:
            result = "FAULT"
            if None in frame_slots:
                # A free frame exists — no eviction needed yet.
                slot = frame_slots.index(None)
                frame_slots[slot] = page
                fifo_queue.append(slot)
            else:
                # Memory is full — evict the page that arrived earliest.
                slot = fifo_queue.popleft()
                replaced_page = frame_slots[slot]
                frame_slots[slot] = page
                fifo_queue.append(slot)

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
