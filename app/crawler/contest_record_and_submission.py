from math import ceil
from typing import Dict, Final, List, Tuple

from loguru import logger

from app.crawler.utils import multi_http_request
from app.db.models import DATA_REGION


async def request_contest_records(
    contest_name: str,
    data_region: DATA_REGION,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Fetch all ranking records of a contest by sending http request per page concurrently
    :param contest_name:
    :param data_region:
    :return:
    """
    base_url: Final[str] = (
        "https://leetcode.com" if data_region == "US" else "https://leetcode.cn"
    )
    logger.info(f"start {base_url=}")
    req = (
        await multi_http_request(
            {
                "req": {
                    "url": f"{base_url}/contest/api/ranking/{contest_name}/",
                    "method": "GET",
                }
            }
        )
    )[0]
    data = req.json()
    user_num = data.get("user_num")
    page_max = ceil(user_num / 25)
    contest_record_list = list()
    nested_submission_list = list()
    url_list = [
        f"{base_url}/contest/api/ranking/{contest_name}/?pagination={page}&region=global"
        for page in range(1, page_max + 1)
    ]
    responses = await multi_http_request(
        {url: {"url": url, "method": "GET"} for url in url_list},
        concurrent_num=5 if data_region == "US" else 10,
    )
    for res in responses:
        if res is None:
            continue
        res_dict = res.json()
        contest_record_list.extend(res_dict.get("total_rank"))
        nested_submission_list.extend(res_dict.get("submissions"))
    logger.success("finished")
    return contest_record_list, nested_submission_list
