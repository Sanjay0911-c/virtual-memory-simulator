"""
Workload service — generates reference strings for the simulator.

Generation only: nothing here runs a page replacement algorithm. The
result is a plain list of page numbers the frontend can drop into the
normal reference-string input and feed to the existing simulate /
compare / frame-analysis endpoints.

Pages are drawn from 0 .. page_range-1. Randomness always comes from a
private random.Random(seed) — never the global RNG — so a given
(type, parameters, seed) always yields the identical string. When the
caller supplies no seed for a random type, one is chosen and RETURNED so
the run can still be reproduced afterwards.
"""

import random
from typing import Dict, List, Optional

from app.services.validation import validate_pages, validate_workload_params

DEFAULT_PATTERN_LENGTH = 4
DEFAULT_WORKING_SET_SIZE = 4
DEFAULT_LOCALITY_PROBABILITY = 0.8
LOCALITY_PHASES = 4  # the working set moves this many times over a locality string

# Types whose output depends on a random draw (and therefore on a seed).
SEEDED_TYPES = {"random", "repeated", "locality"}


def generate_workload(
    workload_type: str,
    length: int,
    page_range: int,
    seed: Optional[int] = None,
    pattern_length: Optional[int] = None,
    working_set_size: Optional[int] = None,
    locality_probability: Optional[float] = None,
) -> Dict:
    wtype = validate_workload_params(
        workload_type, length, page_range, seed, pattern_length, working_set_size, locality_probability
    )

    used_seed = None
    rng = None
    if wtype in SEEDED_TYPES:
        used_seed = seed if seed is not None else random.SystemRandom().randrange(2**32)
        rng = random.Random(used_seed)

    parameters: Dict = {}

    if wtype == "sequential":
        # 0, 1, 2, ... wrapping back to 0 after page_range-1.
        pages = [i % page_range for i in range(length)]

    elif wtype == "random":
        pages = [rng.randrange(page_range) for _ in range(length)]

    elif wtype == "repeated":
        # A fixed pattern of distinct pages, cycled until `length` is reached.
        plen = pattern_length if pattern_length is not None else min(DEFAULT_PATTERN_LENGTH, page_range)
        pattern = rng.sample(range(page_range), plen)
        pages = [pattern[i % plen] for i in range(length)]
        parameters = {"pattern_length": plen, "pattern": pattern}

    else:  # locality
        # Temporal locality: each reference comes from the current working
        # set with probability `prob`, otherwise from anywhere in the range.
        # The working set is re-chosen at the start of each of LOCALITY_PHASES
        # equal-length phases, so the "hot" pages drift over time.
        wsize = working_set_size if working_set_size is not None else min(DEFAULT_WORKING_SET_SIZE, page_range)
        prob = locality_probability if locality_probability is not None else DEFAULT_LOCALITY_PROBABILITY
        phase_len = max(1, -(-length // LOCALITY_PHASES))  # ceil division
        pages = []
        working_set: List[int] = []
        for i in range(length):
            if i % phase_len == 0:
                working_set = rng.sample(range(page_range), wsize)
            if rng.random() < prob:
                pages.append(rng.choice(working_set))
            else:
                pages.append(rng.randrange(page_range))
        parameters = {"working_set_size": wsize, "locality_probability": prob}

    validate_pages(pages)  # same rules as a manually entered string

    return {
        "type": wtype,
        "length": length,
        "page_range": page_range,
        "seed": used_seed,
        "parameters": parameters,
        "pages": pages,
    }
