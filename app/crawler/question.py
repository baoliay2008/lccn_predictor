from typing import Dict, List, Optional

from app.crawler.utils import multi_http_request
from app.db.models import DATA_REGION


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
