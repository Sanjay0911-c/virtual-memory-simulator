"""
Stage 7: API-level tests for POST /api/frame-analysis.

The FIFO fault counts used as "known" expected values below were
computed by directly running simulate_fifo() (see the Stage 7 report
for the exact script) rather than pulled from memory of a textbook —
so these numbers are verified against THIS implementation, not assumed.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Classic textbook Belady's anomaly reference string (Silberschatz-style):
# FIFO faults at frames=3 -> 9, frames=4 -> 10 (an INCREASE despite more memory).
BELADY_PAGES = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

# The reference string used throughout Stages 2-6; FIFO faults here are
# 9, 9, 6, 6 for frames=2..5 -- monotonically non-increasing, no anomaly.
NO_ANOMALY_PAGES = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]


def test_frame_analysis_success_envelope_and_shape():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": NO_ANOMALY_PAGES, "min_frames": 2, "max_frames": 5},
    )
    body = resp.json()

    assert resp.status_code == 200
    assert body["success"] is True
    assert body["error"] is None

    data = body["data"]
    assert data["reference_string"] == NO_ANOMALY_PAGES
    assert data["min_frames"] == 2
    assert data["max_frames"] == 5
    assert [row["frames"] for row in data["sweep"]] == [2, 3, 4, 5]

    for row in data["sweep"]:
        assert set(row["results"].keys()) == {"FIFO", "LRU", "OPTIMAL"}
        for algo_result in row["results"].values():
            assert set(algo_result.keys()) == {
                "algorithm", "total_requests", "page_faults", "page_hits",
                "hit_ratio", "fault_ratio", "replacements",
            }
            # Deliberately lean: no per-step trace in a multi-frame-count sweep.
            assert "steps" not in algo_result

    assert set(data["belady_anomaly"].keys()) == {"detected", "occurrences", "explanation"}
    assert isinstance(data["belady_anomaly"]["explanation"], str)
    assert len(data["belady_anomaly"]["explanation"]) > 0


def test_frame_analysis_fifo_faults_match_individual_simulate_calls():
    # Cross-check: the sweep's per-frame-count FIFO numbers must exactly
    # match calling /api/simulate directly for each of those frame counts
    # -- proving the sweep reuses the same algorithm/service code path
    # rather than computing anything independently.
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": NO_ANOMALY_PAGES, "min_frames": 2, "max_frames": 4},
    )
    sweep = resp.json()["data"]["sweep"]

    for row in sweep:
        direct = client.post(
            "/api/simulate",
            json={"pages": NO_ANOMALY_PAGES, "frames": row["frames"], "algorithm": "FIFO"},
        ).json()["data"]
        assert row["results"]["FIFO"]["page_faults"] == direct["page_faults"]
        assert row["results"]["FIFO"]["page_hits"] == direct["page_hits"]


def test_frame_analysis_detects_known_belady_anomaly():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": BELADY_PAGES, "min_frames": 1, "max_frames": 6},
    )
    data = resp.json()["data"]

    fifo_faults_by_frame = {row["frames"]: row["results"]["FIFO"]["page_faults"] for row in data["sweep"]}
    assert fifo_faults_by_frame == {1: 12, 2: 12, 3: 9, 4: 10, 5: 5, 6: 5}

    belady = data["belady_anomaly"]
    assert belady["detected"] is True
    assert belady["occurrences"] == [
        {"from_frames": 3, "to_frames": 4, "from_faults": 9, "to_faults": 10}
    ]


def test_frame_analysis_no_anomaly_case():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": NO_ANOMALY_PAGES, "min_frames": 2, "max_frames": 5},
    )
    data = resp.json()["data"]

    fifo_faults_by_frame = {row["frames"]: row["results"]["FIFO"]["page_faults"] for row in data["sweep"]}
    assert fifo_faults_by_frame == {2: 9, 3: 9, 4: 6, 5: 6}

    belady = data["belady_anomaly"]
    assert belady["detected"] is False
    assert belady["occurrences"] == []


def test_frame_analysis_single_frame_count_range_has_no_anomaly():
    # A degenerate range (min == max) has nothing to compare -- must not
    # crash and must not claim an anomaly.
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": NO_ANOMALY_PAGES, "min_frames": 3, "max_frames": 3},
    )
    data = resp.json()["data"]
    assert len(data["sweep"]) == 1
    assert data["belady_anomaly"]["detected"] is False
    assert data["belady_anomaly"]["occurrences"] == []


# ---- Invalid input ----

def test_frame_analysis_zero_min_frames_is_invalid_frame_count():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": [1, 2, 3], "min_frames": 0, "max_frames": 3},
    )
    body = resp.json()
    assert resp.status_code == 400
    assert body["error"]["code"] == "INVALID_FRAME_COUNT"


def test_frame_analysis_negative_max_frames_is_invalid_frame_count():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": [1, 2, 3], "min_frames": 1, "max_frames": -2},
    )
    assert resp.json()["error"]["code"] == "INVALID_FRAME_COUNT"


def test_frame_analysis_min_greater_than_max_is_invalid_frame_range():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": [1, 2, 3], "min_frames": 5, "max_frames": 2},
    )
    body = resp.json()
    assert resp.status_code == 400
    assert body["error"]["code"] == "INVALID_FRAME_RANGE"


def test_frame_analysis_range_too_wide_is_invalid_frame_range():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": [1, 2, 3], "min_frames": 1, "max_frames": 100},
    )
    assert resp.json()["error"]["code"] == "INVALID_FRAME_RANGE"


def test_frame_analysis_empty_pages_is_invalid_reference_string():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": [], "min_frames": 1, "max_frames": 3},
    )
    assert resp.json()["error"]["code"] == "INVALID_REFERENCE_STRING"


def test_frame_analysis_missing_field_is_invalid_input():
    resp = client.post("/api/frame-analysis", json={"pages": [1, 2, 3], "min_frames": 1})  # no max_frames
    body = resp.json()
    assert resp.status_code == 422
    assert body["error"]["code"] == "INVALID_INPUT"


def test_frame_analysis_wrong_type_is_invalid_input():
    resp = client.post(
        "/api/frame-analysis",
        json={"pages": [1, 2, 3], "min_frames": "two", "max_frames": 4},
    )
    body = resp.json()
    assert resp.status_code == 422
    assert body["error"]["code"] == "INVALID_INPUT"
