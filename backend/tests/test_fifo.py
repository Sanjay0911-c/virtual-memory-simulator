import pytest

from app.algorithms.fifo import simulate_fifo


def faults(steps):
    return sum(1 for s in steps if s["result"] == "FAULT")


def hits(steps):
    return sum(1 for s in steps if s["result"] == "HIT")


def replacements(steps):
    return sum(1 for s in steps if s["replaced_page"] is not None)


# 10. Known example, manually verified by hand-tracing FIFO:
# pages = 7,0,1,2,0,3,0,4,2,3 ; frames = 3
# Arrival order evictions: 7,0,1,2(evict7),0(hit),3(evict0),0(evict1),4(evict2),2(evict3),3(evict0)
# -> 9 faults, 1 hit (step 5, page 0)
def test_known_textbook_example():
    pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
    steps = simulate_fifo(pages, 3)

    assert len(steps) == 10
    assert faults(steps) == 9
    assert hits(steps) == 1
    assert steps[4]["page"] == 0
    assert steps[4]["result"] == "HIT"  # step 5 (index 4) is the one hit
    # First replacement evicts page 7 (the very first page loaded)
    assert steps[3]["result"] == "FAULT"
    assert steps[3]["replaced_page"] == 7


# 1. Normal reference string with a mix of hits and faults (covered above).

# 2. Repeated pages, immediate reuse.
def test_repeated_page_immediately_reused_is_a_hit():
    pages = [1, 2, 1, 2, 1]
    steps = simulate_fifo(pages, 2)
    assert faults(steps) == 2  # only the first 1 and first 2 fault
    assert hits(steps) == 3


# 3. All unique pages -> every request faults regardless of algorithm.
def test_all_unique_pages_all_fault():
    pages = [1, 2, 3, 4, 5]
    steps = simulate_fifo(pages, 3)
    assert faults(steps) == 5
    assert hits(steps) == 0
    # Replacements only start once the 3 frames are full (steps 4 and 5).
    assert replacements(steps) == 2


# 4. Same page repeated many times -> one fault, then all hits.
def test_same_page_repeated_many_times():
    pages = [5, 5, 5, 5]
    steps = simulate_fifo(pages, 2)
    assert faults(steps) == 1
    assert hits(steps) == 3
    assert steps[-1]["frames"] == [5, None]


# 5. Frames greater than number of unique pages -> no evictions ever.
def test_frames_greater_than_unique_pages_no_replacements():
    pages = [1, 2, 3]
    steps = simulate_fifo(pages, 5)
    assert faults(steps) == 3
    assert replacements(steps) == 0
    assert steps[-1]["frames"] == [1, 2, 3, None, None]


# 6. Frames = 1 -> every distinct-from-previous request faults.
def test_single_frame_always_faults_on_change():
    pages = [1, 2, 3, 1, 2]
    steps = simulate_fifo(pages, 1)
    assert faults(steps) == 5
    assert hits(steps) == 0
    assert steps[-1]["frames"] == [2]


# 7. Reference string shorter than frame count -> all faults, no replacements.
def test_reference_string_shorter_than_frame_count():
    pages = [1, 2]
    steps = simulate_fifo(pages, 5)
    assert faults(steps) == 2
    assert replacements(steps) == 0
    assert steps[-1]["frames"] == [1, 2, None, None, None]


# 8. Empty input -> no steps, no crash.
def test_empty_reference_string_returns_no_steps():
    assert simulate_fifo([], 3) == []


# 9. Invalid input -> frame_count must be positive.
def test_invalid_frame_count_raises():
    with pytest.raises(ValueError):
        simulate_fifo([1, 2, 3], 0)
    with pytest.raises(ValueError):
        simulate_fifo([1, 2, 3], -1)
