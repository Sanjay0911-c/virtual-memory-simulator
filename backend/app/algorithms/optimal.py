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


def simulate_optimal(pages: List[int], frame_count: int, explain: bool = False) -> List[Step]:
    """Run Optimal page replacement over `pages` with `frame_count` frames.

    Frame slots are stable positions, same convention as FIFO/LRU.
    Ties (two resident pages both never used again) are broken
    deterministically by slot order (the page occupying the lowest
    slot index is evicted first).

    If `explain` is True, every step that evicts a page also carries a
    "decision" dict built from the same next-use distances the victim was
    chosen from. The default (False) leaves the step records unchanged.

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
        decision: Optional[dict] = None

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

                resident = [p for p in frame_slots if p is not None]
                distances = {p: next_use_distance(p) for p in resident}
                # max() keeps the FIRST maximum, i.e. the lowest slot among ties.
                victim_page = max(resident, key=distances.__getitem__)
                slot = frame_slots.index(victim_page)
                replaced_page = victim_page
                if explain:
                    decision = _optimal_decision(victim_page, page, step_num, resident, distances)
                frame_slots[slot] = page

        step = {
            "step": step_num,
            "page": page,
            "frames": frame_slots.copy(),
            "result": result,
            "replaced_page": replaced_page,
        }
        if decision is not None:
            step["decision"] = decision
        steps.append(step)

    return steps


def _optimal_decision(
    victim: int, incoming: int, step_num: int, resident: List[int], distances: dict
) -> dict:
    """Evidence for one Optimal eviction. `distances` maps each resident
    page to how many references ahead its next use is (inf = never again);
    it is the exact table the victim was selected from. `next_use` in the
    output is the absolute step number of that next use, or None."""
    candidates = [
        {
            "page": p,
            "next_use": None if distances[p] == float("inf") else step_num + 1 + int(distances[p]),
        }
        for p in resident
    ]
    victim_next = next(c["next_use"] for c in candidates if c["page"] == victim)
    never_used = [c["page"] for c in candidates if c["next_use"] is None]

    uses = ", ".join(
        f"{c['page']} ({'never again' if c['next_use'] is None else 'step ' + str(c['next_use'])})"
        for c in candidates
    )
    if victim_next is None:
        why = f"page {victim} is never used again"
        others = [p for p in never_used if p != victim]
        if others:
            why += (
                f", and so {'is' if len(others) == 1 else 'are'} "
                f"{'page' if len(others) == 1 else 'pages'} {', '.join(str(p) for p in others)}; "
                f"the tie is broken by frame order, so the page in the lowest-numbered frame "
                f"({victim}) is evicted"
            )
    else:
        why = f"page {victim} is not needed until step {victim_next}, the farthest of all resident pages"

    return {
        "policy": "OPTIMAL",
        "victim": victim,
        "candidates": candidates,
        "tie_broken": victim_next is None and len(never_used) > 1,
        "reason": (
            f"Page {incoming} faulted and every frame was full. Optimal evicts the page whose "
            f"next use is farthest in the future: {why}. Next use of each resident page: {uses}."
        ),
    }
