import asyncio
from random import choice
from time import time

import aiohttp

from consts import USER_AGENTS
from scanner import search_for_hrefs, clean_tags, get_pattern, get_template


class Results:
    pages_scanned = set()
    pages_found = set()


async def scan_page(session: aiohttp.ClientSession, start_url: str):
    headers = {
        "User-Agent": choice(USER_AGENTS),
    }
    async with session.get(start_url, headers=headers) as response:
        response.raise_for_status()
        final_url = start_url if not response.history else clean_tags(str(response.url))

        if start_url in Results.pages_scanned:
            return

        print("scanning:", start_url)

        if start_url != final_url:
            print("redirected to:", final_url)
        if get_pattern(start_url, False) != get_pattern(final_url, False):
            return

        html = await response.text()
        template = get_template(final_url)
        links, _ = search_for_hrefs(final_url, template, html)
        Results.pages_found.update(links)
        Results.pages_scanned.update((start_url, final_url))
        unique_links = links - Results.pages_scanned
        print(len(unique_links))

        for link in unique_links:
            await asyncio.create_task(scan_page(session, link), name=clean_tags(link))


async def main(first_url: str):
    async with aiohttp.ClientSession() as session:
        await scan_page(session, first_url)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    t = time()
    url = "http://www.avosetrov.ru/"
    # url = "https://dvmn.org/"
    asyncio.run(main(url))
    r = Results()
    print(f"{time() - t:.2f}")
    print("wot")
