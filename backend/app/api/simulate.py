"""
POST /api/simulate — run ONE page replacement algorithm and return its
full step-by-step trace plus summary metrics.

This route handler does almost nothing itself: parse the (already
type-validated, by Pydantic) request, hand it to the simulation
service, wrap whatever comes back in the standard success envelope.
Any invalid input raises APIError inside the service, which is caught
by the app-level exception handler in main.py — this handler never
needs a try/except of its own.
"""

from fastapi import APIRouter

from app.models.envelope import success_response
from app.models.requests import SimulateRequest
from app.services.simulation_service import run_simulation

router = APIRouter()


@router.post("/api/simulate")
def simulate(payload: SimulateRequest):
    result = run_simulation(payload.pages, payload.frames, payload.algorithm)
    return success_response(result)
