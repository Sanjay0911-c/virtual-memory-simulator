import pytest

from app.algorithms.lru import simulate_lru


def faults(steps):
    return sum(1 for s in steps if s["result"] == "FAULT")


def hits(steps):
    return sum(1 for s in steps if s["result"] == "HIT")


def replacements(steps):
    return sum(1 for s in steps if s["replaced_page"] is not None)


# 10. Known example, manually verified by hand-tracing LRU:
# pages = 7,0,1,2,0,3,0,4,2,3 ; frames = 3
# Hand trace (last_used step per resident page, evict the smallest):
#   7,0,1,2(evict7,lru@1),0(hit,refresh),3(evict1,lru@3),
#   0(hit,refresh),4(evict2,lru@4),2(evict3,lru@6),3(evict0,lru@7)
# -> 8 faults, 2 hits (steps 5 and 7)
def test_known_textbook_example():
    pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
    steps = simulate_lru(pages, 3)

    assert len(steps) == 10
    assert faults(steps) == 8
    assert hits(steps) == 2
    assert steps[4]["result"] == "HIT"  # step 5: page 0
    assert steps[6]["result"] == "HIT"  # step 7: page 0
    # Step 4 (page 2) evicts page 7, the least-recently-used at that point.
    assert steps[3]["replaced_page"] == 7


# 1. Normal string covered above.

# 2. LRU distinguishes itself from FIFO here: touching 1 again keeps it
#    "fresh", so when 4 arrives, 2 (untouched since it loaded) is evicted
#    instead of 1.
def test_lru_evicts_least_recently_touched_not_oldest_loaded():
    pages = [1, 2, 3, 1, 4]
    steps = simulate_lru(pages, 3)
    # After page 1 is re-touched at step 4, 2 is the LRU page (last used step 2).
    assert steps[4]["replaced_page"] == 2


# 3. All unique pages -> every request faults regardless of algorithm.
def test_all_unique_pages_all_fault():
    pages = [1, 2, 3, 4, 5]
    steps = simulate_lru(pages, 3)
    assert faults(steps) == 5
    assert hits(steps) == 0


# 4. Same page repeated many times -> one fault, then all hits.
def test_same_page_repeated_many_times():
    pages = [5, 5, 5, 5]
    steps = simulate_lru(pages, 2)
    assert faults(steps) == 1
    assert hits(steps) == 3


# 5. Frames greater than number of unique pages -> no evictions ever.
def test_frames_greater_than_unique_pages_no_replacements():
    pages = [1, 2, 3]
    steps = simulate_lru(pages, 5)
    assert faults(steps) == 3
    assert replacements(steps) == 0


# 6. Frames = 1 -> identical behavior to FIFO/Optimal (no choice to make).
def test_single_frame_always_faults_on_change():
    pages = [1, 2, 3, 1, 2]
    steps = simulate_lru(pages, 1)
    assert faults(steps) == 5
    assert hits(steps) == 0


# 7. Reference string shorter than frame count -> all faults, no replacements.
def test_reference_string_shorter_than_frame_count():
    pages = [1, 2]
    steps = simulate_lru(pages, 5)
    assert faults(steps) == 2
    assert replacements(steps) == 0


# 8. Empty input -> no steps, no crash.
def test_empty_reference_string_returns_no_steps():
    assert simulate_lru([], 3) == []


# 9. Invalid input -> frame_count must be positive.
def test_invalid_frame_count_raises():
    with pytest.raises(ValueError):
        simulate_lru([1, 2, 3], 0)
    with pytest.raises(ValueError):
        simulate_lru([1, 2, 3], -1)
