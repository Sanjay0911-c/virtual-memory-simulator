"""
API-level tests for POST /api/simulate.

These go through the real FastAPI app (TestClient -> ASGI -> route ->
service -> algorithm module), so they verify the whole chain, not just
the algorithm logic (already covered by test_fifo.py / test_lru.py /
test_optimal.py). Reuses the same hand-verified reference string from
Stage 2 so the numbers here are cross-checked against those unit tests.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

KNOWN_PAGES = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]


def test_simulate_success_envelope_shape():
    resp = client.post("/api/simulate", json={"pages": KNOWN_PAGES, "frames": 3, "algorithm": "LRU"})
    body = resp.json()

    assert resp.status_code == 200
    assert set(body.keys()) == {"success", "data", "error"}
    assert body["success"] is True
    assert body["error"] is None
    assert set(body["data"].keys()) == {
        "algorithm", "total_requests", "page_faults", "page_hits",
        "hit_ratio", "fault_ratio", "replacements", "steps",
    }


def test_simulate_fifo_matches_hand_verified_result():
    resp = client.post("/api/simulate", json={"pages": KNOWN_PAGES, "frames": 3, "algorithm": "FIFO"})
    data = resp.json()["data"]

    assert data["algorithm"] == "FIFO"
    assert data["total_requests"] == 10
    assert data["page_faults"] == 9
    assert data["page_hits"] == 1
    assert data["hit_ratio"] == 10.0
    assert data["fault_ratio"] == 90.0
    assert len(data["steps"]) == 10


def test_simulate_lru_matches_hand_verified_result():
    resp = client.post("/api/simulate", json={"pages": KNOWN_PAGES, "frames": 3, "algorithm": "LRU"})
    data = resp.json()["data"]

    assert data["page_faults"] == 8
    assert data["page_hits"] == 2
    assert data["hit_ratio"] == 20.0
    assert data["fault_ratio"] == 80.0


def test_simulate_optimal_matches_hand_verified_result():
    resp = client.post("/api/simulate", json={"pages": KNOWN_PAGES, "frames": 3, "algorithm": "OPTIMAL"})
    data = resp.json()["data"]

    assert data["page_faults"] == 6
    assert data["page_hits"] == 4
    assert data["hit_ratio"] == 40.0
    assert data["fault_ratio"] == 60.0


def test_simulate_algorithm_name_is_case_insensitive():
    resp = client.post("/api/simulate", json={"pages": [1, 2, 3], "frames": 2, "algorithm": "lru"})
    body = resp.json()

    assert resp.status_code == 200
    assert body["data"]["algorithm"] == "LRU"


def test_simulate_step_shape_matches_spec_example():
    resp = client.post("/api/simulate", json={"pages": [7, 0, 1], "frames": 3, "algorithm": "FIFO"})
    first_step = resp.json()["data"]["steps"][0]

    assert first_step == {
        "step": 1,
        "page": 7,
        "frames": [7, None, None],
        "result": "FAULT",
        "replaced_page": None,
    }


# ---- Error cases: each must hit its specific error code ----

def test_simulate_zero_frames_is_invalid_frame_count():
    resp = client.post("/api/simulate", json={"pages": [1, 2, 3], "frames": 0, "algorithm": "FIFO"})
    body = resp.json()

    assert resp.status_code == 400
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_FRAME_COUNT"


def test_simulate_negative_frames_is_invalid_frame_count():
    resp = client.post("/api/simulate", json={"pages": [1, 2, 3], "frames": -2, "algorithm": "FIFO"})
    assert resp.json()["error"]["code"] == "INVALID_FRAME_COUNT"


def test_simulate_unknown_algorithm_is_invalid_algorithm():
    resp = client.post("/api/simulate", json={"pages": [1, 2, 3], "frames": 2, "algorithm": "MRU"})
    body = resp.json()

    assert resp.status_code == 400
    assert body["error"]["code"] == "INVALID_ALGORITHM"


def test_simulate_empty_pages_is_invalid_reference_string():
    resp = client.post("/api/simulate", json={"pages": [], "frames": 3, "algorithm": "FIFO"})
    body = resp.json()

    assert resp.status_code == 400
    assert body["error"]["code"] == "INVALID_REFERENCE_STRING"


def test_simulate_negative_page_is_invalid_reference_string():
    resp = client.post("/api/simulate", json={"pages": [1, -5, 3], "frames": 2, "algorithm": "FIFO"})
    assert resp.json()["error"]["code"] == "INVALID_REFERENCE_STRING"


def test_simulate_excessively_large_input_is_invalid_reference_string():
    resp = client.post("/api/simulate", json={"pages": list(range(2000)), "frames": 3, "algorithm": "FIFO"})
    assert resp.json()["error"]["code"] == "INVALID_REFERENCE_STRING"


def test_simulate_missing_field_is_invalid_input():
    resp = client.post("/api/simulate", json={"pages": [1, 2, 3], "algorithm": "FIFO"})  # no "frames"
    body = resp.json()

    assert resp.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_INPUT"


def test_simulate_wrong_type_is_invalid_input():
    resp = client.post("/api/simulate", json={"pages": [1, 2, 3], "frames": "three", "algorithm": "FIFO"})
    body = resp.json()

    assert resp.status_code == 422
    assert body["error"]["code"] == "INVALID_INPUT"


def test_simulate_invalid_token_inside_pages_is_invalid_input():
    # A non-integer entry inside the pages array (e.g. someone bypassing the
    # frontend's own client-side parsing and calling the API directly).
    resp = client.post(
        "/api/simulate", json={"pages": [1, "abc", 3], "frames": 2, "algorithm": "FIFO"}
    )
    body = resp.json()

    assert resp.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_INPUT"


def test_simulate_never_returns_a_raw_traceback():
    # Malformed JSON body entirely -> still comes back as our envelope, not a 500 HTML page.
    resp = client.post("/api/simulate", content="not json", headers={"Content-Type": "application/json"})
    body = resp.json()
    assert body["success"] is False
    assert "error" in body
