import asyncio
from random import choice
from time import time

import aiohttp

from consts import USER_AGENTS
from scanner import search_for_hrefs, clean_tags, get_pattern, get_template, split_endpoints


class AsyncParser:
    # TODO: BaseParser class

    def __init__(
            self,
            other_domains=True,
            nesting_limit=0,
            time_limit=0,
            scanned_limit=0,
            found_limit=0,
            ignore_list: list[str] = None,
    ):
        self.other_domains = other_domains
        self.nesting_limit = nesting_limit
        self.ignore_list = [split_endpoints(ignore_sample) for ignore_sample in ignore_list] if ignore_list else None

        self.time_limit = time_limit
        self.scanned_limit = scanned_limit
        self.found_limit = found_limit

        self.pages_scanned = set()
        self.pages_found = set()

    def run(self, first_url: str):
        self.pages_scanned.clear()
        self.pages_found.clear()
        started = time()
        asyncio.run(self.main(first_url))
        print(f"time: {time() - started:.2f}")

    async def main(self, first_url: str):
        async with aiohttp.ClientSession() as session:
            await self.scan_page(session, first_url)

    async def scan_page(self, session: aiohttp.ClientSession, start_url: str):
        if start_url in self.pages_scanned:
            print("already scanned:", start_url)
            return
        headers = {
            "User-Agent": choice(USER_AGENTS),
        }

        try:
            async with session.get(start_url, headers=headers) as response:
                response.raise_for_status()
                final_url = start_url if not response.history else clean_tags(str(response.url))

                if final_url in self.pages_scanned:
                    print("already scanned:", final_url)
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
                self.pages_scanned.update({start_url, final_url})
                unique_links = links - self.pages_scanned

                if unique_links:
                    tasks = [asyncio.create_task(self.scan_page(session, link)) for link in unique_links]
                    await asyncio.gather(*tasks)

        except aiohttp.client.ClientResponseError as e:
            print(f"exception: {e.status} {e.message} {start_url}")


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    t = time()
    url = "https://www.google.com/"
    p = AsyncParser()
    p.run(url)
    print("scanned:", len(p.pages_scanned))
    print("found:", len(p.pages_found))
    print(f"{time() - t:.2f}")
