from typing import Tuple

from app.crawler.utils import multi_http_request
from app.db.models import DATA_REGION


async def request_user_rating_and_attended_contests_count(
    data_region: DATA_REGION,
    username: str,
) -> Tuple[float | None, int | None]:
    """
    request user's rating, attended contests count
    :param data_region:
    :param username:
    :return:
    """
    if data_region == "CN":
        req = (
            await multi_http_request(
                {
                    (data_region, username): {
                        "url": "https://leetcode.cn/graphql/noj-go/",
                        "method": "POST",
                        "json": {
                            "query": """
                                 query userContestRankingInfo($userSlug: String!) {
                                        userContestRanking(userSlug: $userSlug) {
                                            attendedContestsCount
                                            rating
                                        }
                                    }
                                 """,
                            "variables": {"userSlug": username},
                        },
                    }
                }
            )
        )[0]
    else:
        req = (
            await multi_http_request(
                {
                    (data_region, username): {
                        "url": "https://leetcode.com/graphql/",
                        "method": "POST",
                        "json": {
                            "query": """
                                 query getContestRankingData($username: String!) {
                                    userContestRanking(username: $username) {
                                        attendedContestsCount
                                        rating
                                    }
                                 }
                                 """,
                            "variables": {"username": username},
                        },
                    }
                }
            )
        )[0]
    if req is None:
        raise RuntimeError(f"HTTP request failed for {data_region=} {username=}")
    if (graphql_res := req.json().get("data", {}).get("userContestRanking")) is None:
        # Watch out: `None` means that it cannot request information about this user, it should be a new user.
        return None, None
    else:
        return graphql_res.get("rating"), graphql_res.get("attendedContestsCount")
