"""
Tests for opt-in replacement-decision explanations (explain=True).

Expected values were hand-traced, not copied from program output.
Classic string used throughout: 7,0,1,2,0,3,0,4,2,3 with 3 frames.
"""

import random

import pytest
from fastapi.testclient import TestClient

from app.algorithms.fifo import simulate_fifo
from app.algorithms.lru import simulate_lru
from app.algorithms.optimal import simulate_optimal
from app.main import app

client = TestClient(app)

CLASSIC = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
BELADY = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
ALGOS = {"FIFO": simulate_fifo, "LRU": simulate_lru, "OPTIMAL": simulate_optimal}


def by_page(candidates, key):
    return {c["page"]: c[key] for c in candidates}


# ---- FIFO ----

def test_fifo_decision_uses_real_arrival_order():
    steps = simulate_fifo(CLASSIC, 3, explain=True)

    # Step 4 (page 2): queue is 7 (step 1), 0 (step 2), 1 (step 3) -> evict 7.
    d = steps[3]["decision"]
    assert d["policy"] == "FIFO"
    assert d["victim"] == 7 == steps[3]["replaced_page"]
    assert d["candidates"] == [
        {"page": 7, "loaded_at": 1},
        {"page": 0, "loaded_at": 2},
        {"page": 1, "loaded_at": 3},
    ]
    assert "page 7" in d["reason"] and "step 1" in d["reason"]


def test_fifo_ignores_recent_use():
    # Page 0 is HIT at step 5, yet at step 6 it is still the oldest arrival
    # (loaded at step 2) after 7 was replaced by 2 -> FIFO evicts it anyway.
    steps = simulate_fifo(CLASSIC, 3, explain=True)
    assert steps[4]["result"] == "HIT"
    d = steps[5]["decision"]
    assert d["victim"] == 0 == steps[5]["replaced_page"]
    assert d["candidates"] == [
        {"page": 0, "loaded_at": 2},
        {"page": 1, "loaded_at": 3},
        {"page": 2, "loaded_at": 4},
    ]


# ---- LRU ----

def test_lru_decision_reports_last_used_steps():
    steps = simulate_lru(CLASSIC, 3, explain=True)

    d4 = steps[3]["decision"]  # page 2: last use 7@1, 0@2, 1@3 -> evict 7
    assert d4["policy"] == "LRU"
    assert d4["victim"] == 7 == steps[3]["replaced_page"]
    assert by_page(d4["candidates"], "last_used") == {7: 1, 0: 2, 1: 3}

    d6 = steps[5]["decision"]  # page 3: 2@4, 0@5 (hit refreshed it), 1@3 -> evict 1
    assert d6["victim"] == 1 == steps[5]["replaced_page"]
    assert by_page(d6["candidates"], "last_used") == {2: 4, 0: 5, 1: 3}
    assert [c["page"] for c in d6["candidates"]] == [2, 0, 1]  # frame-slot order


def test_lru_victim_has_the_minimum_last_used():
    for step in simulate_lru(BELADY, 3, explain=True):
        if "decision" in step:
            used = by_page(step["decision"]["candidates"], "last_used")
            assert used[step["decision"]["victim"]] == min(used.values())


# ---- Optimal ----

def test_optimal_never_used_again_and_tie_break_by_lowest_frame():
    steps = simulate_optimal(CLASSIC, 3, explain=True)

    # Step 4 (page 2): 7 never used again, 0 next at step 5, 1 never used again.
    # 7 and 1 tie -> lowest frame (7) is evicted.
    d = steps[3]["decision"]
    assert d["policy"] == "OPTIMAL"
    assert d["victim"] == 7 == steps[3]["replaced_page"]
    assert by_page(d["candidates"], "next_use") == {7: None, 0: 5, 1: None}
    assert d["tie_broken"] is True
    assert "never used again" in d["reason"] and "tie" in d["reason"]
    # The victim is named once as the victim; only the OTHER tied page is listed.
    assert "page 7 is never used again, and so is page 1;" in d["reason"]


def test_optimal_single_never_used_page_is_not_a_tie():
    # Step 6 (page 3): frames [2,0,1]; 0 next at 7, 2 next at 9, 1 never.
    d = simulate_optimal(CLASSIC, 3, explain=True)[5]["decision"]
    assert d["victim"] == 1
    assert by_page(d["candidates"], "next_use") == {2: 9, 0: 7, 1: None}
    assert d["tie_broken"] is False


def test_optimal_evicts_farthest_finite_next_use():
    # 1,2,3,1,2 with 2 frames: at step 3 page 1 is next used at step 4,
    # page 2 at step 5 -> page 2 (farthest) is evicted.
    steps = simulate_optimal([1, 2, 3, 1, 2], 2, explain=True)
    d = steps[2]["decision"]
    assert d["victim"] == 2 == steps[2]["replaced_page"]
    assert by_page(d["candidates"], "next_use") == {1: 4, 2: 5}
    assert d["tie_broken"] is False
    assert "step 5" in d["reason"]


# ---- Hits and empty-frame placements carry no decision ----

@pytest.mark.parametrize("name", ALGOS)
def test_hits_and_initial_placements_have_no_decision(name):
    steps = ALGOS[name](CLASSIC, 3, explain=True)
    assert any(s["result"] == "HIT" for s in steps)  # step 5 is a hit for every algorithm
    assert steps[4]["result"] == "HIT"
    for s in steps[:3]:  # first three faults fill empty frames
        assert s["result"] == "FAULT" and s["replaced_page"] is None
        assert "decision" not in s
    for s in steps:
        if s["result"] == "HIT":
            assert "decision" not in s


# ---- Explanations never change behaviour, and always match replaced_page ----

def random_strings():
    rng = random.Random(2024)
    yield BELADY
    yield CLASSIC
    for _ in range(40):
        yield [rng.randrange(7) for _ in range(rng.randrange(1, 40))]


@pytest.mark.parametrize("name", ALGOS)
def test_explain_does_not_change_simulation(name):
    for pages in random_strings():
        for frames in (1, 2, 3, 4, 6):
            plain = ALGOS[name](pages, frames)
            explained = ALGOS[name](pages, frames, explain=True)
            assert len(plain) == len(explained)
            for p, e in zip(plain, explained):
                assert {k: v for k, v in e.items() if k != "decision"} == p


@pytest.mark.parametrize("name", ALGOS)
def test_decision_victim_always_matches_replaced_page(name):
    for pages in random_strings():
        for frames in (1, 2, 3, 4):
            previous_frames = [None] * frames
            for s in ALGOS[name](pages, frames, explain=True):
                if s["replaced_page"] is None:
                    assert "decision" not in s
                else:
                    d = s["decision"]
                    assert d["victim"] == s["replaced_page"]
                    # candidates are exactly the pages resident before this step
                    assert sorted(c["page"] for c in d["candidates"]) == sorted(
                        p for p in previous_frames if p is not None
                    )
                    assert isinstance(d["reason"], str) and d["reason"]
                previous_frames = s["frames"]


def test_default_steps_have_no_decision_key():
    for name, func in ALGOS.items():
        assert all("decision" not in s for s in func(CLASSIC, 3))


def test_optimal_tie_break_matches_documented_lowest_slot_rule():
    # Frames fill as [1,2,3]; page 4 then faults while 1,2,3 are all never
    # used again -> victim must be the page in slot 0, i.e. page 1.
    d = simulate_optimal([1, 2, 3, 4], 3, explain=True)[3]["decision"]
    assert d["victim"] == 1
    assert d["tie_broken"] is True
    assert all(c["next_use"] is None for c in d["candidates"])


# ---- API ----

def post(explain=None, algorithm="FIFO", pages=CLASSIC, frames=3):
    body = {"pages": pages, "frames": frames, "algorithm": algorithm}
    if explain is not None:
        body["explain"] = explain
    return client.post("/api/simulate", json=body)


def test_api_default_has_no_decisions_and_same_as_explicit_false():
    default = post().json()["data"]
    explicit_false = post(explain=False).json()["data"]
    assert default == explicit_false
    assert all("decision" not in s for s in default["steps"])


@pytest.mark.parametrize("algorithm", ["FIFO", "LRU", "OPTIMAL"])
def test_api_explain_true_adds_only_decisions(algorithm):
    plain = post(algorithm=algorithm).json()["data"]
    explained = post(explain=True, algorithm=algorithm).json()["data"]

    # Same summary metrics...
    for key in ("algorithm", "total_requests", "page_faults", "page_hits",
                "hit_ratio", "fault_ratio", "replacements"):
        assert explained[key] == plain[key]
    # ...same steps apart from the added decision on replacement steps.
    for p, e in zip(plain["steps"], explained["steps"]):
        assert {k: v for k, v in e.items() if k != "decision"} == p
        assert ("decision" in e) == (e["replaced_page"] is not None)
        if "decision" in e:
            assert e["decision"]["victim"] == e["replaced_page"]
    assert explained["replacements"] > 0


def test_api_explain_must_be_boolean():
    resp = post(explain="banana")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_INPUT"


def test_compare_and_frame_analysis_are_unaffected():
    cmp_ = client.post("/api/compare", json={"pages": CLASSIC, "frames": 3}).json()["data"]
    for result in cmp_["results"].values():
        assert all("decision" not in s for s in result["steps"])

    fa = client.post(
        "/api/frame-analysis", json={"pages": CLASSIC, "min_frames": 2, "max_frames": 4}
    ).json()["data"]
    for row in fa["sweep"]:
        for result in row["results"].values():
            assert "steps" not in result
