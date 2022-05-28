import asyncio
from datetime import datetime
from functools import lru_cache
from typing import List

import numpy as np
from beanie.odm.operators.update.general import Set
from tqdm import tqdm
from numba import jit

from app.crawler.contests import save_predict_contest
from app.crawler.users import update_users_from_a_contest
from app.db.models import User, ContestRecordPredict


async def fill_old_rating(record: ContestRecordPredict):
    user = await User.find_one(
        User.username == record.username,
        User.data_region == record.data_region,
    )
    if not user:
        record.old_rating = 1500
        record.attendedContestsCount = 0
    else:
        record.old_rating = user.rating
        record.attendedContestsCount = user.attendedContestsCount
    await record.save()


@lru_cache
def fk_for_delta_coefficient(k):
    # TODO: cache all possible k value(prefix array calculate) when starting program, just save a dict in memory.
    # Or, when k is big enough, return 2/9 directly.
    return 1 / (1 + sum((5 / 7) ** i for i in range(k + 1)))


@jit(nopython=True, fastmath=True, parallel=True)
def expected_win_rate(vector_element, constant):
    # I tested this function, result had shown this function has a quite decent performance.
    # TODO: write a benchmark note.
    return 1 / (1 + np.power(10, (constant - vector_element) / 400))


async def predict_contest(
        contest_name: str,
        update_user_using_prediction: bool = False,
) -> None:
    """
    core predict function using official contest rating algorithm.
    :param contest_name:
    :param update_user_using_prediction: use for biweekly contest because next day's weekly contest needs the latest.
    :return:
    """
    print("start run predict_contest")
    await save_predict_contest(contest_name)
    await update_users_from_a_contest(contest_name)
    records: List[ContestRecordPredict] = (
        await ContestRecordPredict.find(
            ContestRecordPredict.contest_name == contest_name,
            ContestRecordPredict.score != 0,
        )
        .sort(ContestRecordPredict.rank)
        .to_list()
    )
    tasks = (
        fill_old_rating(record)
        for record in records
    )
    await asyncio.gather(*tasks)

    rank_array = np.array([record.rank for record in records])
    rating_array = np.array([record.old_rating for record in records])
    k_array = np.array([record.attendedContestsCount for record in records])

    expected_rating_list = list()
    coefficient_of_delta_list = list()

    for i in tqdm(range(len(rank_array))):
        # no need to filter itself, add all then minus 0.5 is the same.
        # + 1 - 0.5 = + 0.5 works because including i=j is more convenient, can reuse expected_win_rate function below.
        expected_rank = np.sum(expected_win_rate(rank_array, rank_array[i])) + 0.5
        mean_rank = np.sqrt(expected_rank * rating_array[i])
        # Use binary search to find the expected rating, now set 15 for loops
        # TODO: could set a minimal [lo, hi] range to break the for loops in advance, which could be accurate enough.
        # Newton's method should be faster to solve this kind of problem, but the derivative of this function is not
        # easy to get(I don't know for now), maybe slower overall.
        lo, hi = 0, 4000  # 4000 could be big enough, max rating now is 3686.
        target = mean_rank - 1
        # for t in range(15):
        while hi - lo > 0.1:
            # if hi - lo < 0.5:
            #     break
            mid = lo + (hi - lo) / 2
            approximation = np.sum(expected_win_rate(rank_array, mid))
            if approximation < target:
                hi = mid
            else:
                lo = mid
        expected_rating = mid
        coefficient_of_delta = fk_for_delta_coefficient(k_array[i])
        expected_rating_list.append(expected_rating)
        coefficient_of_delta_list.append(coefficient_of_delta)
    expected_rating_array = np.array(expected_rating_list)
    coefficient_of_delta_array = np.array(coefficient_of_delta_list)
    delta_array = coefficient_of_delta_array * (expected_rating_array - rating_array)
    new_rating_array = rating_array + delta_array

    # update ContestRecordPredict collection
    tasks = list()
    for record, new_rating, delta in zip(records, new_rating_array, delta_array):
        tasks.append(
            ContestRecordPredict.find_one(
                ContestRecordPredict.id == record.id,
            ).update(
                Set(
                    {
                        ContestRecordPredict.delta_rating: delta,
                        ContestRecordPredict.new_rating: new_rating,
                        ContestRecordPredict.predict_time: datetime.utcnow(),
                    }
                )
            )
        )
    await asyncio.gather(*tasks)
    print(f"predict_contest finished updating ContestRecordPredict")
    if update_user_using_prediction:
        print(f"immediately write predicted result back into User collection.")
        tasks = (
            await User.find_one(
                User.username == record.username,
                User.data_region == record.data_region,
            ).update(
                Set(
                    {
                        User.rating: record.new_rating,
                        User.attendedContestsCount: record.attendedContestsCount + 1,
                        User.update_time: datetime.utcnow(),
                    }
                )
            ) for record in records
        )
        await asyncio.gather(*tasks)
