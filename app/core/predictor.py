import asyncio
from datetime import datetime
import math
from functools import lru_cache
import time

import pandas as pd
import numpy as np
from beanie.odm.operators.update.general import Set
from tqdm import tqdm
from numba import jit

from app.crawler.rank import save_temporary_contest
from app.crawler.users import insert_users_of_a_contest
from app.db.models import User, ContestPredict


async def fill_old_rating(record: ContestPredict):
    user = await User.find_one(User.username == record.username)
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


async def predict_contest(contest_name):
    # await save_temporary_contest(contest_name)
    # await insert_users_of_a_contest(contest_name)
    records = (
        await ContestPredict.find(ContestPredict.contest_name == contest_name)
        .sort(ContestPredict.rank)
        .to_list()
    )
    # tasks = (
    #     fill_old_rating(record)
    #     for record in records
    # )
    # await asyncio.gather(*tasks)
    t0 = time.time()
    df = pd.DataFrame(
        [
            {
                "username": record.username,
                "R": record.old_rating,
                "k": record.attendedContestsCount,
                "Rank": None,
                # cannot use record.rank as Rank directly, calculate using finish_time
                # because same score and finish_time should have same rank
                "score": record.score * (-1),
                "finish_time": record.finish_time,
                "ERank": None,
                "m": None,
                "ER": None,
                "fk": None,
                "delta": None,
                "new_rating": None,
            }
            for record in records
        ]
    )
    print(f"to pandas DataFrame cost {time.time()-t0} seconds")
    df.to_csv("tmp/weekly_294_raw.csv", index=False)
    # df = pd.read_csv("tmp/weekly_294_raw.csv")
    df["Rank"] = df[["score", "finish_time"]].apply(tuple, axis=1).rank(method="min")

    rating_vector = df.R.to_numpy()
    rank_vector = df.Rank.to_numpy()
    k_vector = df.k.to_numpy()

    e_rank_list = list()
    m_list = list()
    er_list = list()
    fk_list = list()

    for i in tqdm(range(len(rating_vector))):
        # no need to filter itself, add all then minus 0.5 is the same.
        # so, then + 1 - 0.5 = + 0.5 because include i=j is more convenient, can reuse expected_win_rate function.
        e_rank = np.sum(expected_win_rate(rating_vector, rating_vector[i])) + 0.5
        m = np.sqrt(e_rank * rank_vector[i])
        # Use binary search to find the expected rating, now set 15 for loops
        # TODO: could set a minimal [lo, hi] range to break the for loops in advance, which could be accurate enough.
        # Newton's method should be faster to solve this kind of problem, but the derivative of this function is not
        # easy to get(I don't know for now), maybe slower overall.
        lo, hi = 0, 4000
        target = m - 1
        for t in range(15):
            # if hi - lo < 0.5:
            #     break
            mid = lo + (hi - lo) / 2
            tmp = np.sum(expected_win_rate(rating_vector, mid))
            if tmp < target:
                hi = mid
            else:
                lo = mid
        er = mid
        fk = fk_for_delta_coefficient(k_vector[i])
        e_rank_list.append(e_rank)
        m_list.append(m)
        er_list.append(er)
        fk_list.append(fk)
    df["ERank"] = e_rank_list
    df["m"] = m_list
    df["ER"] = er_list
    df["fk"] = fk_list
    df["delta"] = df["fk"] * (df["ER"] - df["R"])
    df["new_rating"] = df["R"] + df["delta"]
    df.to_csv("tmp/weekly_294_predicted.csv", index=False)
    # df = pd.read_csv("tmp/weekly_294_predicted.csv")
    print(df)
    tasks = list()
    for index, row in df.iterrows():
        tasks.append(
            ContestPredict.find_one(
                ContestPredict.username == row.username,
                ContestPredict.finish_time == row.finish_time,  # change to data_region, I didn't save if when sorting.
            ).update(
                Set(
                    {
                        ContestPredict.new_rating: row.new_rating,
                        ContestPredict.delta_rating: row.delta,
                        ContestPredict.predict_time: datetime.utcnow(),
                    }
                )
            )
        )
    print(len(tasks))
    await asyncio.gather(*tasks)

