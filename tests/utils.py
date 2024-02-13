from typing import Final

import numpy as np

# Ensure that the prediction error for rating deltas for EACH participant is within the specified precision limit
RATING_DELTA_PRECISION: Final[float] = 0.05


def read_data_contest_prediction_first():
    with open("tests/tests_data/contest_prediction_1.npy", "rb") as f:
        data = np.load(f)
        ks = data[:, 0]
        ranks = data[:, 1]
        old_ratings = data[:, 2]
        new_ratings = data[:, 3]
        return ks, ranks, old_ratings, new_ratings
