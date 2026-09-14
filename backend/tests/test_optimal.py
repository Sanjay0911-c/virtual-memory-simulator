import pytest

from app.algorithms.optimal import simulate_optimal


def faults(steps):
    return sum(1 for s in steps if s["result"] == "FAULT")


def hits(steps):
    return sum(1 for s in steps if s["result"] == "HIT")


def replacements(steps):
    return sum(1 for s in steps if s["replaced_page"] is not None)


# 10. Known example, manually verified by hand-tracing Optimal (MIN):
# pages = 7,0,1,2,0,3,0,4,2,3 ; frames = 3
# Step 4 (page 2, frames full with 7,0,1): 7 and 1 are never used again
# (tie), 0 is used again immediately -> evict 7 (first among tied,
# lowest slot index).
# Step 6 (page 3, frames full with 2,0,1): 1 never used again -> evict 1.
# Step 8 (page 4, frames full with 2,0,3): 0 never used again -> evict 0.
# After that, 2 (step 9) and 3 (step 10) are both already resident -> hits.
# -> 6 faults, 4 hits (this is the fewest faults any algorithm can achieve
# on this reference string with 3 frames).
def test_known_textbook_example():
    pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
    steps = simulate_optimal(pages, 3)

    assert len(steps) == 10
    assert faults(steps) == 6
    assert hits(steps) == 4
    assert steps[3]["replaced_page"] == 7  # step 4: page 2 evicts 7
    assert steps[5]["replaced_page"] == 1  # step 6: page 3 evicts 1
    assert steps[7]["replaced_page"] == 0  # step 8: page 4 evicts 0
    assert steps[8]["result"] == "HIT"  # step 9: page 2, already resident
    assert steps[9]["result"] == "HIT"  # step 10: page 3, already resident


# Optimal should never do worse than FIFO or LRU on the same input —
# this is the whole point of it being the theoretical best case.
def test_optimal_is_at_least_as_good_as_fifo_and_lru_on_known_example():
    from app.algorithms.fifo import simulate_fifo
    from app.algorithms.lru import simulate_lru

    pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
    optimal_faults = faults(simulate_optimal(pages, 3))
    fifo_faults = faults(simulate_fifo(pages, 3))
    lru_faults = faults(simulate_lru(pages, 3))

    assert optimal_faults <= fifo_faults
    assert optimal_faults <= lru_faults


# 3. All unique pages -> every request faults regardless of algorithm.
def test_all_unique_pages_all_fault():
    pages = [1, 2, 3, 4, 5]
    steps = simulate_optimal(pages, 3)
    assert faults(steps) == 5
    assert hits(steps) == 0


# 4. Same page repeated many times -> one fault, then all hits.
def test_same_page_repeated_many_times():
    pages = [5, 5, 5, 5]
    steps = simulate_optimal(pages, 2)
    assert faults(steps) == 1
    assert hits(steps) == 3


# 5. Frames greater than number of unique pages -> no evictions ever.
def test_frames_greater_than_unique_pages_no_replacements():
    pages = [1, 2, 3]
    steps = simulate_optimal(pages, 5)
    assert faults(steps) == 3
    assert replacements(steps) == 0


# 6. Frames = 1 -> identical behavior to FIFO/LRU (no choice to make).
def test_single_frame_always_faults_on_change():
    pages = [1, 2, 3, 1, 2]
    steps = simulate_optimal(pages, 1)
    assert faults(steps) == 5
    assert hits(steps) == 0


# 7. Reference string shorter than frame count -> all faults, no replacements.
def test_reference_string_shorter_than_frame_count():
    pages = [1, 2]
    steps = simulate_optimal(pages, 5)
    assert faults(steps) == 2
    assert replacements(steps) == 0


# 8. Empty input -> no steps, no crash.
def test_empty_reference_string_returns_no_steps():
    assert simulate_optimal([], 3) == []


# 9. Invalid input -> frame_count must be positive.
def test_invalid_frame_count_raises():
    with pytest.raises(ValueError):
        simulate_optimal([1, 2, 3], 0)
    with pytest.raises(ValueError):
        simulate_optimal([1, 2, 3], -1)
