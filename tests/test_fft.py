from typing import Final

import numpy as np

from app.core.fft import fft_delta

RATING_DELTA_PRECISION: Final[float] = 0.05


def test_fft_delta():
    """
    Test function for the fft_delta function.

    Loads test data from a NumPy file containing columns: ks, ranks, old_ratings, new_ratings.
    Calculates delta_ratings using fft_delta function and checks if the resulting new_ratings
    match the expected values within a specified precision.

    Raises:
        AssertionError: If the calculated ratings deviate from the expected ratings
                        by more than RATING_DELTA_PRECISION.
    """

    with open("tests/test_data/contest_k_rating_test.npy", "rb") as f:
        data = np.load(f)
        ks = data[:, 0]
        ranks = data[:, 1]
        old_ratings = data[:, 2]
        new_ratings = data[:, 3]

        delta_ratings = fft_delta(ranks, old_ratings, ks)
        testing_new_ratings = old_ratings + delta_ratings

        errors = np.abs(new_ratings - testing_new_ratings)
        assert np.all(
            errors < RATING_DELTA_PRECISION
        ), f"Elo delta test failed. Some errors are not within {RATING_DELTA_PRECISION=}."
