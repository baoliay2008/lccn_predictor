from datetime import datetime
from typing import List

import numpy as np
from beanie.odm.operators.update.general import Set
from loguru import logger

from app.core.elo import elo_delta
from app.db.models import Contest, ContestRecordPredict, User
from app.utils import exception_logger_reraise, gather_with_limited_concurrency


async def update_rating_immediately(
    records: List[ContestRecordPredict],
) -> None:
    """
    Update users' rating and attendedContestsCount (if it's biweekly contest)
    :param records:
    :return:
    """
    logger.info("immediately write predicted result back into User collection")
    tasks = [
        User.find_one(
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
        )
        for record in records
    ]
    await gather_with_limited_concurrency(tasks, max_con_num=50)
    logger.success("finished updating User using predicted result")


@exception_logger_reraise
async def predict_contest(
    contest_name: str,
) -> None:
    """
    Core predict function using official elo rating algorithm
    :param contest_name:
    :return:
    """
    records = (
        await ContestRecordPredict.find(
            ContestRecordPredict.contest_name == contest_name,
            ContestRecordPredict.score != 0,
        )
        .sort(ContestRecordPredict.rank)
        .to_list()
    )

    rank_array = np.array([record.rank for record in records])
    rating_array = np.array([record.old_rating for record in records])
    k_array = np.array([record.attendedContestsCount for record in records])
    # core prediction
    delta_rating_array = elo_delta(rank_array, rating_array, k_array)
    new_rating_array = rating_array + delta_rating_array

    # update ContestRecordPredict collection
    predict_time = datetime.utcnow()
    for i, record in enumerate(records):
        record.delta_rating = delta_rating_array[i]
        record.new_rating = new_rating_array[i]
        record.predict_time = predict_time
    tasks = [record.save() for record in records]
    await gather_with_limited_concurrency(tasks, max_con_num=50)
    logger.success("predict_contest finished updating ContestRecordPredict")

    if contest_name.lower().startswith("bi"):
        # for biweekly contests only, because next day's weekly contest needs the latest rating
        await update_rating_immediately(records)

    # update Contest collection to indicate that this contest has been predicted.
    # by design, predictions should only be run once.
    await Contest.find_one(Contest.titleSlug == contest_name).update(
        Set(
            {
                Contest.predict_time: datetime.utcnow(),
            }
        )
    )
    logger.info("finished updating predict_time in Contest database")
