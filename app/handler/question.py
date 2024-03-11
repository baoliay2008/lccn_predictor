import asyncio
from datetime import datetime, timedelta
from typing import List

from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.question import request_question_list
from app.db.models import Question, Submission
from app.utils import gather_with_limited_concurrency, get_contest_start_time


async def real_time_count_at_time_point(
    contest_name: str,
    question_id: int,
    time_point: datetime,
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


async def save_questions_real_time_count(
    contest_name: str,
    delta_minutes: int = 1,
) -> None:
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
        tasks = [
            real_time_count_at_time_point(
                contest_name, question.question_id, time_point
            )
            for time_point in time_series
        ]
        question.real_time_count = await gather_with_limited_concurrency(tasks)
        await question.save()
    logger.success("finished")


async def save_questions(
    contest_name: str,
) -> List[Question]:
    """
    For the past contests, fetch questions list and fill into MongoDB
    :param contest_name:
    :return:
    """
    try:
        question_list = await request_question_list(contest_name)
        time_point = datetime.utcnow()
        additional_fields = {
            "contest_name": contest_name,
        }
        questions = list()
        for idx, question in enumerate(question_list):
            question.pop("id")
            question.update({"qi": idx + 1})
            questions.append(Question.model_validate(question | additional_fields))
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
            for question_obj in questions
        )
        await asyncio.gather(*tasks)
        # Old questions may change, could delete here.
        await Question.find(
            Question.contest_name == contest_name,
            Question.update_time < time_point,
        ).delete()
        logger.success("finished")
        return questions
    except Exception as e:
        logger.error(
            f"failed to fill questions fields for {contest_name=} {questions=} {e=}"
        )
