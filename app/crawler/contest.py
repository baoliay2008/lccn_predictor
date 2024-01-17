import re
from typing import Dict, List

from loguru import logger

from app.crawler.utils import multi_http_request


async def request_past_contests(
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
    logger.info(f"{max_page_num=} {len(past_contests)=}")
    return past_contests


async def request_contest_homepage_text():
    req = (
        await multi_http_request(
            {
                "req": {
                    "url": "https://leetcode.com/contest/",
                    "method": "GET",
                }
            }
        )
    )[0]
    return req.text


async def request_next_two_contests() -> List[Dict]:
    """
    save two coming contests
    :return:
    """
    contest_page_text = await request_contest_homepage_text()
    build_id_search = re.search(
        re.compile(r'"buildId":\s*"(.*?)",'),
        contest_page_text,
    )
    if not build_id_search:
        logger.error("cannot find buildId")
        return []
    build_id = build_id_search.groups()[0]
    next_data = (
        await multi_http_request(
            {
                "req": {
                    "url": f"https://leetcode.com/_next/data/{build_id}/contest.json",
                    "method": "GET",
                }
            }
        )
    )[0].json()
    top_two_contests = list()
    for queries in (
        next_data.get("pageProps", {}).get("dehydratedState", {}).get("queries", {})
    ):
        if "topTwoContests" in (data := queries.get("state", {}).get("data", {})):
            top_two_contests = data.get("topTwoContests")
            break
    if not top_two_contests:
        logger.error("cannot find topTwoContests")
        return []
    logger.info(f"{top_two_contests=}")
    return top_two_contests


async def request_all_past_contests() -> List[Dict]:
    """
    Save past contests
    :return:
    """
    contest_page_text = await request_contest_homepage_text()
    max_page_num_search = re.search(
        re.compile(r'"pageNum":\s*(\d+)'),
        contest_page_text,
    )
    if not max_page_num_search:
        logger.error("cannot find pageNum")
        return []
    max_page_num = int(max_page_num_search.groups()[0])
    all_past_contests = await request_past_contests(max_page_num)
    return all_past_contests


async def request_recent_contests() -> List[Dict]:
    """
    Save 10 past contests on the first page
    :return:
    """
    # 10 contests on the first page, which are enough
    ten_past_contests = await request_past_contests(1)
    return ten_past_contests
