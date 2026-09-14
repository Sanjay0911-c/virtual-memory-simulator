"""
Shared step-record type.

fifo.py, lru.py, and optimal.py each return a list of these — one dict
per page reference, showing frame contents after that reference was
processed. The three algorithm modules previously each defined an
identical `Step` TypedDict; that was pure duplication (a type
declaration, not logic), so it now lives in exactly one place. This
does not merge any algorithm behavior — FIFO, LRU, and Optimal remain
fully separate modules/functions, as required.
"""

from typing import List, Optional, TypedDict


class Step(TypedDict):
    step: int
    page: int
    frames: List[Optional[int]]
    result: str
    replaced_page: Optional[int]
