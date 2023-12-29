from typing import Final

import numpy as np

from app.core.elo import elo_delta

ELO_DELTA_PRECISION: Final[float] = 0.05


def test_elo_delta():
    """
    Test the Elo rating system implementation.

    Loads test data, calculates Elo deltas, and checks if the errors
    between expected new ratings and calculated new ratings are within
    a specified precision.

    Raises:
        AssertionError: If not all errors are within the specified precision.
    """

    with open("tests/test_data/contest_k_rating_test.npy", "rb") as f:
        data = np.load(f)
        ks = data[:, 0]
        ranks = data[:, 1]
        old_ratings = data[:, 2]
        new_ratings = data[:, 3]

        delta_ratings = elo_delta(ranks, old_ratings, ks)
        testing_new_ratings = old_ratings + delta_ratings

        errors = np.abs(new_ratings - testing_new_ratings)
        assert np.all(
            errors < ELO_DELTA_PRECISION
        ), f"Elo delta test failed. Some errors are not within {ELO_DELTA_PRECISION=}."
