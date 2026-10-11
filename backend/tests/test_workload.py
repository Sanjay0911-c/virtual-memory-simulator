"""
Tests for workload (reference-string) generation: service-level
properties of each pattern type, seed determinism, validation, and the
POST /api/workload endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.validation import APIError, MAX_REFERENCE_LENGTH
from app.services.workload_service import generate_workload

client = TestClient(app)


def post(**overrides):
    body = {"type": "random", "length": 20, "page_range": 8}
    body.update(overrides)
    return client.post("/api/workload", json=body)


# ---- Each workload type ----

def test_sequential_counts_up_and_wraps():
    result = generate_workload("sequential", 7, 3)
    assert result["pages"] == [0, 1, 2, 0, 1, 2, 0]
    assert result["seed"] is None  # nothing random about it


def test_sequential_shorter_than_range():
    assert generate_workload("sequential", 3, 10)["pages"] == [0, 1, 2]


def test_random_has_requested_length_and_stays_in_range():
    pages = generate_workload("random", 200, 6, seed=1)["pages"]
    assert len(pages) == 200
    assert all(isinstance(p, int) and 0 <= p < 6 for p in pages)
    assert len(set(pages)) > 1  # not degenerate


def test_repeated_cycles_a_fixed_distinct_pattern():
    result = generate_workload("repeated", 14, 10, seed=5, pattern_length=3)
    pattern = result["parameters"]["pattern"]
    assert len(pattern) == 3 and len(set(pattern)) == 3
    assert all(0 <= p < 10 for p in pattern)
    assert result["pages"] == [pattern[i % 3] for i in range(14)]


def test_repeated_default_pattern_length_is_capped_by_page_range():
    result = generate_workload("repeated", 10, 2, seed=1)
    assert result["parameters"]["pattern_length"] == 2


def test_locality_with_probability_one_stays_inside_each_working_set():
    # length 8 -> 4 phases of 2 references; with p=1 every page must come
    # from that phase's working set (size 2 -> at most 2 distinct per phase).
    pages = generate_workload("locality", 8, 50, seed=3, working_set_size=2, locality_probability=1)["pages"]
    for start in range(0, 8, 2):
        assert len(set(pages[start:start + 2])) <= 2
    assert all(0 <= p < 50 for p in pages)


def test_locality_is_more_concentrated_than_uniform_random():
    loc = generate_workload("locality", 400, 50, seed=11, working_set_size=3, locality_probability=0.95)["pages"]
    rnd = generate_workload("random", 400, 50, seed=11)["pages"]
    assert len(set(loc)) < len(set(rnd))


def test_locality_probability_zero_is_allowed():
    pages = generate_workload("locality", 30, 5, seed=2, locality_probability=0)["pages"]
    assert len(pages) == 30


def test_type_is_case_insensitive():
    assert generate_workload("SEQUENTIAL", 3, 3)["type"] == "sequential"


# ---- Determinism / seeds ----

@pytest.mark.parametrize("wtype", ["random", "repeated", "locality"])
def test_same_seed_gives_identical_output(wtype):
    a = generate_workload(wtype, 100, 12, seed=42)
    b = generate_workload(wtype, 100, 12, seed=42)
    assert a == b
    assert a["seed"] == 42


@pytest.mark.parametrize("wtype", ["random", "locality"])
def test_different_seeds_give_different_output(wtype):
    assert generate_workload(wtype, 100, 12, seed=1)["pages"] != generate_workload(wtype, 100, 12, seed=2)["pages"]


@pytest.mark.parametrize("wtype", ["random", "repeated", "locality"])
def test_unseeded_run_returns_a_seed_that_reproduces_it(wtype):
    first = generate_workload(wtype, 60, 9)
    assert isinstance(first["seed"], int)
    again = generate_workload(wtype, 60, 9, seed=first["seed"])
    assert again["pages"] == first["pages"]


def test_generation_does_not_touch_global_random_state():
    import random

    random.seed(123)
    expected = random.random()
    random.seed(123)
    generate_workload("random", 50, 10, seed=7)
    assert random.random() == expected


# ---- Validation ----

@pytest.mark.parametrize(
    "kwargs",
    [
        dict(workload_type="bogus", length=5, page_range=5),
        dict(workload_type="random", length=0, page_range=5),
        dict(workload_type="random", length=-3, page_range=5),
        dict(workload_type="random", length=MAX_REFERENCE_LENGTH + 1, page_range=5),
        dict(workload_type="random", length=5, page_range=0),
        dict(workload_type="random", length=5, page_range=5, seed=-1),
        dict(workload_type="random", length=5, page_range=5, seed=2**32),
        dict(workload_type="repeated", length=5, page_range=3, pattern_length=4),
        dict(workload_type="repeated", length=5, page_range=3, pattern_length=0),
        dict(workload_type="locality", length=5, page_range=3, working_set_size=4),
        dict(workload_type="locality", length=5, page_range=3, working_set_size=0),
        dict(workload_type="locality", length=5, page_range=3, locality_probability=1.5),
        dict(workload_type="locality", length=5, page_range=3, locality_probability=-0.1),
    ],
)
def test_invalid_parameters_raise_invalid_workload(kwargs):
    with pytest.raises(APIError) as exc:
        generate_workload(**kwargs)
    assert exc.value.code == "INVALID_WORKLOAD"


def test_max_length_is_allowed_and_matches_manual_limit():
    assert len(generate_workload("sequential", MAX_REFERENCE_LENGTH, 10)["pages"]) == MAX_REFERENCE_LENGTH


# ---- API endpoint ----

def test_api_success_envelope_and_shape():
    resp = post(type="locality", seed=9)
    body = resp.json()
    assert resp.status_code == 200
    assert body["success"] is True and body["error"] is None
    data = body["data"]
    assert set(data.keys()) == {"type", "length", "page_range", "seed", "parameters", "pages"}
    assert data["type"] == "locality" and data["seed"] == 9
    assert len(data["pages"]) == 20


def test_api_is_reproducible_with_seed():
    assert post(seed=77).json()["data"]["pages"] == post(seed=77).json()["data"]["pages"]


def test_api_output_feeds_existing_endpoints():
    pages = post(type="repeated", length=30, page_range=6, seed=4).json()["data"]["pages"]

    sim = client.post("/api/simulate", json={"pages": pages, "frames": 3, "algorithm": "FIFO"})
    assert sim.status_code == 200 and sim.json()["data"]["total_requests"] == 30

    cmp_ = client.post("/api/compare", json={"pages": pages, "frames": 3})
    assert cmp_.status_code == 200

    fa = client.post("/api/frame-analysis", json={"pages": pages, "min_frames": 1, "max_frames": 4})
    assert fa.status_code == 200


def test_api_invalid_workload_uses_error_envelope():
    resp = post(type="bogus")
    body = resp.json()
    assert resp.status_code == 400
    assert body["success"] is False and body["data"] is None
    assert body["error"]["code"] == "INVALID_WORKLOAD"


def test_api_too_long_is_rejected():
    resp = post(length=MAX_REFERENCE_LENGTH + 1)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_WORKLOAD"


def test_api_missing_field_is_invalid_input():
    resp = client.post("/api/workload", json={"type": "random", "length": 5})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_INPUT"
