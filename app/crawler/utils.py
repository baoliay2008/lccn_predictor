from typing import List, Dict, Optional
from collections import deque, defaultdict
import httpx
import asyncio


async def multi_http_request(
    multi_requests: Dict,
    concurrent_num: int = 5,
) -> List[Optional[httpx.Response]]:
    response_mapper = defaultdict(int)  # values means: [int: retried time / Response: successful result]
    crawler_queue = deque(multi_requests.items())
    total_num = len(crawler_queue)
    # gradually adjust wait_time by detect number of failed requests in the last round.
    wait_time = 0
    while crawler_queue:
        requests_list = list()
        # gradually increase wait_time according to max retry times
        # wait_time = response_mapper[job_queue[-1][0]]
        while len(requests_list) < concurrent_num and crawler_queue:
            key, request = crawler_queue.popleft()
            if response_mapper[key] >= 10:
                continue
            requests_list.append((key, request))
        if not requests_list:
            break
        print(f"remaining={len(crawler_queue) / total_num * 100 :.2f}% wait_time={wait_time} "
              f"requests_list={[(key, response_mapper[key]) for key, request in requests_list]}")
        await asyncio.sleep(wait_time)
        async with httpx.AsyncClient() as client:
            tasks = [client.request(**request) for key, request in requests_list]
            response_list = await asyncio.gather(*tasks, return_exceptions=True)
            wait_time = 0
            for response, (key, request) in zip(response_list, requests_list):
                if isinstance(response, httpx.Response) and response.status_code == 200:
                    # TODO: Very high memory usage here when saving response directly, say, if run 20000 requests.
                    response_mapper[key] = response
                else:
                    # response could be an Exception here
                    print(f"multi_http_request error: "
                          f"{response.text if isinstance(response, httpx.Response) else response}")
                    response_mapper[key] += 1
                    wait_time += 1
                    crawler_queue.append((key, request))
    return [
        None if isinstance(response, int) else response
        for key, response in response_mapper.items()
    ]
