import numpy as np
import pytest

from app.core.fft import fft_delta
from tests.utils import RATING_DELTA_PRECISION, read_data_contest_prediction_first


@pytest.fixture
def data_contest_prediction_first():
    return read_data_contest_prediction_first()


def test_fft_delta(data_contest_prediction_first):
    """
    Test function for the fft_delta function.

    Raises:
        AssertionError: If not all errors are within the specified precision.
    """

    ks, ranks, old_ratings, new_ratings = data_contest_prediction_first

    delta_ratings = fft_delta(ranks, old_ratings, ks)
    testing_new_ratings = old_ratings + delta_ratings

    errors = np.abs(new_ratings - testing_new_ratings)
    assert np.all(
        errors < RATING_DELTA_PRECISION
    ), f"FFT delta test failed. Some errors are not within {RATING_DELTA_PRECISION=}."
