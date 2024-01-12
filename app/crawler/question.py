import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.utils import multi_http_request
from app.db.models import DATA_REGION, Question, Submission
from app.utils import get_contest_start_time


async def request_questions(
    contest_name: str,
    data_region: DATA_REGION,
) -> Optional[List[Dict]]:
    """
    Send HTTP request to get questions data of a given contest
    :param contest_name:
    :param data_region:
    :return:
    """
    if data_region == "US":
        url = f"https://leetcode.com/contest/api/info/{contest_name}/"
    elif data_region == "CN":
        url = f"https://leetcode.cn/contest/api/info/{contest_name}/"
    else:
        raise ValueError(f"{data_region=}")
    data = (
        await multi_http_request(
            {
                "req": {
                    "url": url,
                    "method": "GET",
                }
            }
        )
    )[0].json()
    return data.get("questions")


async def finish_count_at_time_point(
    contest_name: str, question_id: int, time_point: datetime
) -> int:
    """
    For a single question, count its finished submission at a given time point.
    :param contest_name:
    :param question_id:
    :param time_point:
    :return:
    """
    return await Submission.find(
        Submission.contest_name == contest_name,
        Submission.question_id == question_id,
        Submission.date <= time_point,
    ).count()


async def save_question_finish_count(contest_name: str, delta_minutes: int = 1) -> None:
    """
    For every delta_minutes, count accepted submissions for each question.
    :param contest_name:
    :param delta_minutes:
    :return:
    """
    time_series = list()
    start_time = get_contest_start_time(contest_name)
    end_time = start_time + timedelta(minutes=90)
    while (start_time := start_time + timedelta(minutes=delta_minutes)) <= end_time:
        time_series.append(start_time)
    logger.info(f"{contest_name=} {time_series=}")
    questions = await Question.find(
        Question.contest_name == contest_name,
    ).to_list()
    for question in questions:
        tasks = (
            finish_count_at_time_point(contest_name, question.question_id, time_point)
            for time_point in time_series
        )
        question.real_time_count = await asyncio.gather(*tasks)
        await question.save()
    logger.success("finished")


async def fill_questions_field(contest_name: str, questions: List[Dict]) -> None:
    """
    For the past contests, fetch questions list and fill into MongoDB
    :param contest_name:
    :param questions:
    :return:
    """
    try:
        time_point = datetime.utcnow()
        additional_fields = {
            "contest_name": contest_name,
        }
        question_objs = list()
        for idx, question in enumerate(questions):
            question.pop("id")
            question.update({"qi": idx + 1})
            question_objs.append(Question.model_validate(question | additional_fields))
        tasks = (
            Question.find_one(
                Question.question_id == question_obj.question_id,
                Question.contest_name == contest_name,
            ).upsert(
                Set(
                    {
                        Question.credit: question_obj.credit,
                        Question.title: question_obj.title,
                        Question.title_slug: question_obj.title_slug,
                        Question.update_time: question_obj.update_time,
                        Question.qi: question_obj.qi,
                    }
                ),
                on_insert=question_obj,
            )
            for question_obj in question_objs
        )
        await asyncio.gather(*tasks)
        # Old questions may change, could delete here.
        await Question.find(
            Question.contest_name == contest_name,
            Question.update_time < time_point,
        ).delete()
        logger.success("finished")
    except Exception as e:
        logger.error(
            f"failed to fill questions fields for {contest_name=} {questions=} {e=}"
        )
