import numpy as np
from scipy.signal import fftconvolve

from app.core.elo import delta_coefficients

EXPAND_SIZE = 100
MAX_RATING = 4000 * EXPAND_SIZE


def pre_calc_convolution(old_rating: np.ndarray) -> np.ndarray:
    """
    Pre-calculate convolution values for the Elo rating update.
    :param old_rating:
    :return:
    """
    f = 1 / (
        1 + np.power(10, np.arange(-MAX_RATING, MAX_RATING + 1) / (400 * EXPAND_SIZE))
    )
    g = np.bincount(np.round(old_rating * EXPAND_SIZE).astype(int))
    convolution = fftconvolve(f, g, mode="full")
    convolution = convolution[: 2 * MAX_RATING + 1]
    return convolution


def get_expected_rank(convolution: np.ndarray, x: int) -> float:
    """
    Get the expected rank based on pre-calculated convolution values.
    :param convolution:
    :param x:
    :return:
    """
    return convolution[x + MAX_RATING] + 0.5


def get_equation_left(convolution: np.ndarray, x: int) -> float:
    """
    Get the left side of equation for expected rating based on pre-calculated convolution values
    :param convolution:
    :param x:
    :return:
    """
    return convolution[x + MAX_RATING] + 1


def binary_search_expected_rating(convolution: np.ndarray, mean_rank: float) -> int:
    """
    Perform binary search to find the expected rating for a given mean rank.
    :param convolution:
    :param mean_rank:
    :return:
    """
    lo, hi = 0, MAX_RATING
    while lo < hi:
        mid = (lo + hi) // 2
        if get_equation_left(convolution, mid) < mean_rank:
            hi = mid
        else:
            lo = mid + 1
    return mid


def get_expected_rating(rank: int, rating: float, convolution: np.ndarray) -> float:
    """
    Calculate the expected rating based on current rank, rating, and pre-calculated convolution.
    :param rank:
    :param rating:
    :param convolution:
    :return:
    """
    expected_rank = get_expected_rank(convolution, round(rating * EXPAND_SIZE))
    mean_rank = np.sqrt(expected_rank * rank)
    return binary_search_expected_rating(convolution, mean_rank) / EXPAND_SIZE


def fft_delta(ranks: np.ndarray, ratings: np.ndarray, ks: np.ndarray) -> np.ndarray:
    """
    Calculate Elo rating changes using Fast Fourier Transform (FFT)
    :param ranks:
    :param ratings:
    :param ks:
    :return:
    """
    convolution = pre_calc_convolution(ratings)
    expected_ratings = list()
    for i in range(len(ranks)):
        rank = ranks[i]
        rating = ratings[i]
        expected_ratings.append(get_expected_rating(rank, rating, convolution))
    delta_ratings = (np.array(expected_ratings) - ratings) * delta_coefficients(ks)
    return delta_ratings
