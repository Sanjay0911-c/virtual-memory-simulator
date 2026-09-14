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

from typing import List

from pydantic import BaseModel


class SimulateRequest(BaseModel):
    pages: List[int]
    frames: int
    algorithm: str


class CompareRequest(BaseModel):
    pages: List[int]
    frames: int


class FrameAnalysisRequest(BaseModel):
    pages: List[int]
    min_frames: int
    max_frames: int
