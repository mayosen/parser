import asyncio
from pprint import pprint
from random import choice
from time import time

import aiohttp

from consts import USER_AGENTS
from parsers.base_parser import BaseParser
from scanner import search_for_hrefs, get_template, get_pattern, clean_tags


class AsyncParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def run(self, first_url: str) -> tuple[dict, list, list]:
        self.pages_scanned.clear()
        self.pages_found.clear()
        started = time()
        asyncio.run(self.main(first_url))
        times = {}
        times["total"] = round(time() - started, 2)
        times["mean"] = round(times["total"] / len(self.pages_scanned), 2)
        return times, list(self.pages_scanned), sorted(self.pages_found)

    async def main(self, first_url: str):
        async with aiohttp.ClientSession() as session:
            await self.scan_page(session, first_url)

    async def scan_page(self, session: aiohttp.ClientSession, start_url: str):
        if start_url in self.pages_scanned:
            # print("already scanned:", start_url)
            return
        headers = {
            "User-Agent": choice(USER_AGENTS),
        }

        try:
            async with session.get(start_url, headers=headers) as response:
                response.raise_for_status()
                final_url = start_url if not response.history else clean_tags(str(response.url))

                if final_url in self.pages_scanned:
                    # print("already scanned:", final_url)
                    return

                print("scanning:", start_url)
                self.pages_scanned.update({start_url, final_url})

                if start_url != final_url:
                    print("redirected to:", final_url)
                    if get_pattern(start_url, full=False) != get_pattern(final_url, full=False):
                        print("skipped:", final_url)
                        return

                try:
                    html = await response.text()
                except UnicodeDecodeError as e:
                    print(f"{e.reason}")
                    return

                template = get_template(final_url)
                links, _ = search_for_hrefs(
                    final_url, template, html, self.other_domains, self.nesting_limit, self.ignore_list,
                )
                self.pages_found.update(links)
                unique_links = links - self.pages_scanned

                if unique_links:
                    tasks = [asyncio.create_task(self.scan_page(session, link)) for link in unique_links]
                    await asyncio.gather(*tasks)

        except aiohttp.client.ClientResponseError as e:
            print(f"exception: {e.status} {e.message} {start_url}")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    url = "http://www.avosetrov.ru/"
    p = AsyncParser()
    times, _, _ = p.run(url)
    pprint(times)
    print("scanned:", len(p.pages_scanned))
    print("found:", len(p.pages_found))
