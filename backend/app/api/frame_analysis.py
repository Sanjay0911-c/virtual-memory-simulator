"""
POST /api/frame-analysis — Stage 7 addition.

Runs FIFO, LRU, and Optimal across a range of frame counts on the same
reference string, and flags Belady's anomaly in the FIFO series (fault
count going UP as frame count goes up). Same thin-handler pattern as
simulate.py/compare.py: parse the (Pydantic-validated) request, hand it
to the service, wrap the result in the standard success envelope. Any
invalid input raises APIError inside the service/validation layer,
caught by the same app-level exception handlers already registered in
main.py — nothing new needed there for errors.
"""

from fastapi import APIRouter

from app.models.envelope import success_response
from app.models.requests import FrameAnalysisRequest
from app.services.simulation_service import run_frame_analysis

router = APIRouter()


@router.post("/api/frame-analysis")
def frame_analysis(payload: FrameAnalysisRequest):
    result = run_frame_analysis(payload.pages, payload.min_frames, payload.max_frames)
    return success_response(result)
