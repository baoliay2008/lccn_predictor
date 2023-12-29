from functools import lru_cache
from typing import Final

import numpy as np
from numba import jit


@lru_cache
def pre_sum_of_sigma(k: int) -> float:
    """
    Series cache
    :param k:
    :return:
    """
    # if not isinstance(k, int):
    #     raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError(f"{k=}, pre_sum's index less than zero!")
    return (5 / 7) ** k + pre_sum_of_sigma(k - 1) if k >= 1 else 1


@lru_cache
def adjustment_for_delta_coefficient(k: int) -> float:
    """
    This function could also be `return 1 / (1 + sum((5 / 7) ** i for i in range(k + 1)))`
    but use a `pre_sum_of_sigma` function(which is also cached) is faster.
    When k is big enough, result approximately equals to 2/9.
    :param k:
    :return:
    """
    return 1 / (1 + pre_sum_of_sigma(k)) if k <= 100 else 2 / 9


def delta_coefficients(ks: np.ndarray) -> np.ndarray:
    """
    Calculate delta coefficients for the given input array.
    :param ks:
    :return:
    """
    vectorized_func = np.vectorize(adjustment_for_delta_coefficient)
    return vectorized_func(ks)


@jit(nopython=True, fastmath=True, parallel=True)
def expected_win_rate(vector: np.ndarray, scalar: float) -> np.ndarray:
    """
    Calculate the expected win rate based on the Elo rating system.
    Test result had shown this function has a quite decent performance.
    :param vector:
    :param scalar:
    :return:
    """
    return 1 / (1 + np.power(10, (scalar - vector) / 400))


@jit(nopython=True, fastmath=True, parallel=True)
def binary_search_expected_rating(mean_rank: int, all_rating: np.ndarray) -> float:
    """
    Perform binary search to find the rating corresponding to the given mean rank.
    :param mean_rank:
    :param all_rating:
    :return:
    """
    target = mean_rank - 1
    lo, hi = 0, 4000
    max_iteration = 25
    precision: Final[float] = 0.01
    while hi - lo > precision and max_iteration >= 0:
        mid = lo + (hi - lo) / 2
        if np.sum(expected_win_rate(all_rating, mid)) < target:
            hi = mid
        else:
            lo = mid
        max_iteration -= 1
    return mid


@jit(nopython=True, fastmath=True, parallel=True)
def get_expected_rating(rank: int, rating: float, all_rating: np.ndarray) -> float:
    """
    Calculate the expected rating based on the given rank, player rating, and array of all ratings.
    :param rank:
    :param rating:
    :param all_rating:
    :return:
    """
    expected_rank = np.sum(expected_win_rate(all_rating, rating)) + 0.5
    mean_rank = np.sqrt(expected_rank * rank)
    return binary_search_expected_rating(mean_rank, all_rating)


def elo_delta(ranks: np.ndarray, ratings: np.ndarray, ks: np.ndarray) -> np.ndarray:
    """
    Calculate the Elo rating changes (delta) based on the given ranks, current ratings, and coefficients.
    :param ranks:
    :param ratings:
    :param ks:
    :return:
    """
    expected_ratings = list()
    for i in range(len(ranks)):
        rank = ranks[i]
        rating = ratings[i]
        expected_ratings.append(get_expected_rating(rank, rating, ratings))
    delta_ratings = (np.array(expected_ratings) - ratings) * delta_coefficients(ks)
    return delta_ratings
