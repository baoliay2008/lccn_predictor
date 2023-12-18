import asyncio
import re
from datetime import datetime
from typing import Dict, List

import httpx
from beanie.odm.operators.update.general import Set
from loguru import logger

from app.crawler.utils import multi_http_request
from app.db.models import Contest, Question
from app.utils import exception_logger_reraise


async def multi_upsert_contests(
    contests: List[Dict],
    past: bool,
) -> None:
    """
    Save meta data of Contests into MongoDB
    :param contests:
    :param past:
    :return:
    """
    tasks = list()
    for contest_dict in contests:
        try:
            contest_dict["past"] = past
            contest_dict["endTime"] = (
                contest_dict["startTime"] + contest_dict["duration"]
            )
            logger.debug(f"{contest_dict=}")
            contest = Contest.parse_obj(contest_dict)
            logger.debug(f"{contest=}")
        except Exception as e:
            logger.exception(
                f"parse contest_dict error {e}. skip upsert {contest_dict=}"
            )
            continue
        tasks.append(
            Contest.find_one(Contest.titleSlug == contest.titleSlug,).upsert(
                Set(
                    {
                        Contest.update_time: contest.update_time,
                        Contest.title: contest.title,
                        Contest.startTime: contest.startTime,
                        Contest.duration: contest.duration,
                        Contest.past: past,
                        Contest.endTime: contest.endTime,
                    }
                ),
                on_insert=contest,
            )
        )
    await asyncio.gather(*tasks)
    logger.success("finished")


async def multi_request_past_contests(
    max_page_num: int,
) -> List[Dict]:
    """
    Fetch past contests information
    :param max_page_num:
    :return:
    """
    response_list = await multi_http_request(
        {
            page_num: {
                "url": "https://leetcode.com/graphql/",
                "method": "POST",
                "json": {
                    "query": """
                            query pastContests($pageNo: Int) {
                                pastContests(pageNo: $pageNo) {
                                    data { title titleSlug startTime duration }
                                }
                            }
                            """,
                    "variables": {"pageNo": page_num},
                },
            }
            for page_num in range(1, max_page_num + 1)
        },
        concurrent_num=10,
    )
    past_contests = list()
    for response in response_list:
        past_contests.extend(
            response.json().get("data", {}).get("pastContests", {}).get("data", [])
        )
    logger.success("finished")
    return past_contests


async def save_past_contests() -> None:
    """
    Save past contests
    :return:
    """
    contest_page_text = httpx.get("https://leetcode.com/contest/").text
    max_page_num_search = re.search(
        re.compile(r'"pageNum":\s*(\d+)'),
        contest_page_text,
    )
    if not max_page_num_search:
        logger.error("cannot find pageNum")
        return
    max_page_num = int(max_page_num_search.groups()[0])
    past_contests = await multi_request_past_contests(max_page_num)
    await multi_upsert_contests(past_contests, past=True)
    logger.success("finished")


async def save_top_two_contests() -> None:
    """
    save two coming contests
    :return:
    """
    contest_page_text = httpx.get("https://leetcode.com/contest/").text
    build_id_search = re.search(
        re.compile(r'"buildId":\s*"(.*?)",'),
        contest_page_text,
    )
    if not build_id_search:
        logger.error("cannot find buildId")
        return
    build_id = build_id_search.groups()[0]
    next_data = httpx.get(
        f"https://leetcode.com/_next/data/{build_id}/contest.json"
    ).json()
    top_two_contests = list()
    for queries in (
        next_data.get("pageProps", {}).get("dehydratedState", {}).get("queries", {})
    ):
        if "topTwoContests" in (data := queries.get("state", {}).get("data", {})):
            top_two_contests = data.get("topTwoContests")
            break
    if not top_two_contests:
        logger.error("cannot find topTwoContests")
        return
    logger.info(f"{top_two_contests=}")
    await multi_upsert_contests(top_two_contests, past=False)
    logger.success("finished")


@exception_logger_reraise
async def save_all_contests() -> None:
    """
    Save past contests and top two coming contests
    :return:
    """
    await save_top_two_contests()
    await save_past_contests()
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
            question_objs.append(Question.parse_obj(question | additional_fields))
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
