"""
POST /api/compare — run FIFO, LRU, and Optimal on the SAME reference
string and frame count in a single request, so the frontend can show
a side-by-side comparison without three separate round trips.
"""

from fastapi import APIRouter

from app.models.envelope import success_response
from app.models.requests import CompareRequest
from app.services.simulation_service import run_comparison

router = APIRouter()


@router.post("/api/compare")
def compare(payload: CompareRequest):
    result = run_comparison(payload.pages, payload.frames)
    return success_response(result)
