"""
Pydantic request models — define the SHAPE of what the API accepts.

These only enforce basic types (pages is a list of ints, frames is an
int, algorithm is a string). FastAPI/Pydantic rejects requests that
don't match these types automatically, before our code ever runs; that
rejection is caught in main.py and reshaped into our standardized error
envelope (code INVALID_INPUT).

Deeper, OS-meaningful rules — frames > 0, no negative page numbers, a
recognized algorithm name — are semantic, not just structural, so they
live in services/validation.py instead, where they can raise the more
specific error codes (INVALID_FRAME_COUNT, INVALID_REFERENCE_STRING,
INVALID_ALGORITHM) the project spec calls for.
"""

from typing import List, Optional

from pydantic import BaseModel


class SimulateRequest(BaseModel):
    pages: List[int]
    frames: int
    algorithm: str
    # Opt-in: when true, replacement steps include a "decision" block.
    explain: bool = False


class CompareRequest(BaseModel):
    pages: List[int]
    frames: int


class FrameAnalysisRequest(BaseModel):
    pages: List[int]
    min_frames: int
    max_frames: int


class WorkloadRequest(BaseModel):
    """Parameters for POST /api/workload. `type`, `length` and `page_range`
    are always required; the optional fields apply to specific workload
    types (see services/workload_service.py) and fall back to documented
    defaults when omitted."""

    type: str
    length: int
    page_range: int
    seed: Optional[int] = None
    pattern_length: Optional[int] = None
    working_set_size: Optional[int] = None
    locality_probability: Optional[float] = None
