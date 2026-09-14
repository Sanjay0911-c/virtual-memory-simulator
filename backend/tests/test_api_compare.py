"""
API-level tests for POST /api/compare.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

KNOWN_PAGES = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]


def test_compare_success_envelope_and_shape():
    resp = client.post("/api/compare", json={"pages": KNOWN_PAGES, "frames": 3})
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert body["error"] is None

    data = body["data"]
    assert data["reference_string"] == KNOWN_PAGES
    assert data["frames"] == 3
    assert set(data["results"].keys()) == {"FIFO", "LRU", "OPTIMAL"}

    for algo_result in data["results"].values():
        assert set(algo_result.keys()) == {
            "algorithm", "total_requests", "page_faults", "page_hits",
            "hit_ratio", "fault_ratio", "replacements", "steps",
        }


def test_compare_matches_hand_verified_results():
    resp = client.post("/api/compare", json={"pages": KNOWN_PAGES, "frames": 3})
    results = resp.json()["data"]["results"]

    assert results["FIFO"]["page_faults"] == 9
    assert results["LRU"]["page_faults"] == 8
    assert results["OPTIMAL"]["page_faults"] == 6

    # Optimal must never fault more than FIFO or LRU on the same input.
    assert results["OPTIMAL"]["page_faults"] <= results["FIFO"]["page_faults"]
    assert results["OPTIMAL"]["page_faults"] <= results["LRU"]["page_faults"]


def test_compare_invalid_frame_count():
    resp = client.post("/api/compare", json={"pages": [1, 2, 3], "frames": 0})
    body = resp.json()

    assert resp.status_code == 400
    assert body["error"]["code"] == "INVALID_FRAME_COUNT"


def test_compare_empty_pages():
    resp = client.post("/api/compare", json={"pages": [], "frames": 3})
    assert resp.json()["error"]["code"] == "INVALID_REFERENCE_STRING"


def test_compare_missing_field_is_invalid_input():
    resp = client.post("/api/compare", json={"pages": [1, 2, 3]})  # no "frames"
    body = resp.json()

    assert resp.status_code == 422
    assert body["error"]["code"] == "INVALID_INPUT"
