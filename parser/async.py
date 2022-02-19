import asyncio
import aiohttp
import requests

from main import scan_page, search_for_hrefs, get_main_url
from time import time
from statistics import mean


links_to_test = [
    "https://dvmn.org/contacts/",
    "https://dvmn.org/encyclopedia/",
    "https://dvmn.org/encyclopedia/about-chatbots/chat-bot-design/",
    "https://dvmn.org/encyclopedia/about-chatbots/long-polling/",
    "https://dvmn.org/encyclopedia/about-chatbots/ptbot-tutorial/",
    "https://dvmn.org/encyclopedia/about-chatbots/webhook/",
    "https://dvmn.org/encyclopedia/api-docs/yandex-geocoder-api/",
    "https://dvmn.org/encyclopedia/async_python/coroutine_bomb/",
    "https://dvmn.org/encyclopedia/async_python/coroutines/",
    "https://dvmn.org/encyclopedia/async_python/how-to-stop-coroutine/",
    "https://dvmn.org/encyclopedia/async_python/split_corutine/",
    "https://dvmn.org/encyclopedia/async_python/why_async/",
]


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        elapsed = time() - start
        print(elapsed)
        return res
    return wrapper


@timeit
def test_sync():
    links = []

    for url in links_to_test:
        page = requests.get(url).text
        # links_on_page, _ = scan_page(url)
        # links.extend(links_on_page)

    return links


async def run_for_pages():
    links = set()

    async with aiohttp.ClientSession() as session:
        for url in links_to_test:
            async with session.get(url) as response:
                print("scanning:", url)
                page = await response.text()

            main_url = get_main_url(url)
            clean_links, dirt_links = search_for_hrefs(main_url, page)
            links.update(clean_links)

    return links


if __name__ == "__main__":
    # test_sync()

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    start = time()
    links = asyncio.run(run_for_pages())
    print(time() - start)
    print(links)


