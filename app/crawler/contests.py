import httpx


async def post_past_contests(page_num):
    async with httpx.AsyncClient() as client:  # TODO: take out client to reuse.
        response = await client.post(
            url="https://leetcode.com/graphql/",
            json={
                "query": """
                        query pastContests($pageNo: Int) {
                            pastContests(pageNo: $pageNo) {
                            pageNum
                            currentPage
                            totalNum
                            numPerPage
                            data {
                                title
                                titleSlug
                                startTime
                                originStartTime
                                cardImg
                                sponsors {
                                    name
                                    lightLogo
                                    darkLogo
                                    }
                                }
                            }
                        }
                        """,
                "variables": {"pageNo": page_num},
            },
        )
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(
                f"post_past_contests request failed. page_num {page_num}, {response.status_code}"
            )
            return {}


async def get_past_contests():
    response = httpx.get("https://leetcode.com/_next/data/8WLj7v8Ws6MgUpP6OdjtN/contest.json")
    # topTwoContests
    # pageNum
    # page_max = response.json().get("")