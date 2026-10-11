"""
POST /api/workload — generate a reference string (sequential, random,
repeated or locality-based). Same thin-handler pattern as the other
routes: Pydantic validates the shape, the service validates the meaning
and generates, and the result is wrapped in the standard envelope. It
only GENERATES a string; it never runs a simulation.
"""

from fastapi import APIRouter

from app.models.envelope import success_response
from app.models.requests import WorkloadRequest
from app.services.workload_service import generate_workload

router = APIRouter()


@router.post("/api/workload")
def workload(payload: WorkloadRequest):
    result = generate_workload(
        payload.type,
        payload.length,
        payload.page_range,
        payload.seed,
        payload.pattern_length,
        payload.working_set_size,
        payload.locality_probability,
    )
    return success_response(result)
