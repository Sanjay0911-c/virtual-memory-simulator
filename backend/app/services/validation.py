"""
Semantic input validation for the simulation API.

This sits between the API layer (which only checks basic JSON shape
via Pydantic) and the algorithm modules (which assume their input is
already valid). It exists so that a bad request — an empty reference
string, a zero frame count, an unknown algorithm name — produces a
clear, specific error message instead of an obscure crash somewhere
deep in the simulation logic. This is the "Never allow invalid input
to crash the application" requirement, enforced in one place.
"""

from typing import List

MAX_REFERENCE_LENGTH = 1000
MAX_FRAME_RANGE_SPAN = 50  # guard against an absurdly wide frame-count sweep
VALID_ALGORITHMS = {"FIFO", "LRU", "OPTIMAL"}


class APIError(Exception):
    """Raised for any semantically invalid request.

    Carries an error `code` (one of the project's standardized codes)
    and a human-readable `message`, plus the HTTP status to respond
    with. main.py's exception handler turns this into the standardized
    error envelope.
    """

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_pages(pages: List[int]) -> None:
    if pages is None or len(pages) == 0:
        raise APIError("INVALID_REFERENCE_STRING", "Reference string cannot be empty")

    if len(pages) > MAX_REFERENCE_LENGTH:
        raise APIError(
            "INVALID_REFERENCE_STRING",
            f"Reference string is too long (max {MAX_REFERENCE_LENGTH} page requests)",
        )

    for p in pages:
        if isinstance(p, bool) or not isinstance(p, int) or p < 0:
            raise APIError(
                "INVALID_REFERENCE_STRING",
                "Reference string must contain only non-negative integers",
            )


def validate_frames(frames: int) -> None:
    if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
        raise APIError("INVALID_FRAME_COUNT", "Number of frames must be greater than zero")


def validate_frame_range(min_frames: int, max_frames: int) -> None:
    """Used by the frame-count analysis endpoint (a sweep over several
    frame counts, min_frames..max_frames inclusive). Each bound is
    validated the same way a single frame count is (INVALID_FRAME_COUNT);
    an invalid ORDERING or an unreasonably wide sweep is a separate,
    more specific problem (INVALID_FRAME_RANGE).
    """
    for label, value in (("min_frames", min_frames), ("max_frames", max_frames)):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise APIError("INVALID_FRAME_COUNT", f"{label} must be a positive integer")

    if min_frames > max_frames:
        raise APIError(
            "INVALID_FRAME_RANGE",
            "min_frames cannot be greater than max_frames",
        )

    span = max_frames - min_frames + 1
    if span > MAX_FRAME_RANGE_SPAN:
        raise APIError(
            "INVALID_FRAME_RANGE",
            f"Frame range is too wide (max {MAX_FRAME_RANGE_SPAN} frame counts per request)",
        )


def validate_algorithm(algorithm: str) -> str:
    """Returns the normalized (uppercase) algorithm name, or raises APIError."""
    if not isinstance(algorithm, str) or algorithm.upper() not in VALID_ALGORITHMS:
        raise APIError(
            "INVALID_ALGORITHM",
            f"Algorithm must be one of {sorted(VALID_ALGORITHMS)}",
        )
    return algorithm.upper()
