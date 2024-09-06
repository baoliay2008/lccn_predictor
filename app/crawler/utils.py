import asyncio
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0",
}


async def multi_http_request(
    multi_requests: Dict,
    concurrent_num: int = 5,
    retry_num: int = 10,
) -> List[Optional[httpx.Response]]:
    """
    Simple HTTP requests queue with speed control and retry automatically, hopefully can get corresponding response.
    Failed response would be `None` but not a `response` object, so invokers MUST verify for None values.
    Notice that `multi_requests` is `Dict` but not `Sequence` so that data accessing would be easier.
    Because all the stuff are in memory, so DO NOT pass a long `multi_requests` in especially when `response` is huge.
    :param multi_requests:
    :param concurrent_num:
    :param retry_num:
    :return:
    """
    # response_mapper value means: [int: retried times / Response: successful result]
    response_mapper: Dict[Any, int | httpx.Response] = defaultdict(int)
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
            if response_mapper[key] >= retry_num:
                logger.error(
                    f"request reached max retry_num. {key=}, req={multi_requests[key]}"
                )
                continue
            requests_list.append((key, request))
        if not requests_list:
            break
        logger.info(
            f"remaining={len(crawler_queue) / total_num * 100 :.2f}% wait_time={wait_time} "
            f"requests_list={[(key, response_mapper[key]) for key, request in requests_list]}"
        )
        await asyncio.sleep(wait_time)
        async with httpx.AsyncClient(headers=headers) as client:
            tasks = [client.request(**request) for key, request in requests_list]
            response_list = await asyncio.gather(*tasks, return_exceptions=True)
            wait_time = 0
            for response, (key, request) in zip(response_list, requests_list):
                if isinstance(response, httpx.Response) and response.status_code == 200:
                    # TODO: Very high memory usage here when saving response directly, say, if run 20000 requests.
                    response_mapper[key] = response
                else:
                    # response could be an Exception here
                    logger.warning(
                        f"multi_http_request error: {request=} "
                        f"response.status_code: "
                        f"{response.status_code if isinstance(response, httpx.Response) else response}"
                    )
                    response_mapper[key] += 1
                    wait_time += 1
                    crawler_queue.append((key, request))
    return [
        None if isinstance(response, int) else response
        for key, response in response_mapper.items()
    ]
