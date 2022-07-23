import asyncio
from abc import abstractmethod, ABC
from collections import deque
from random import choice
from statistics import mean
from time import time

import aiohttp
import requests
from requests import HTTPError

from consts import USER_AGENTS
from scanner import split_endpoints, get_template, search_for_hrefs, get_pattern, clean_tags


class BaseParser(ABC):
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

    @abstractmethod
    def run(self, url: str) -> tuple[dict, list, list]:
        raise NotImplementedError


class SyncParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, first_url: str) -> tuple[dict, list, list]:
        """
        Makes a pass through all the pages found and scans it.
        """

        pages_to_scan = deque((first_url,))
        self.pages_scanned.clear()
        self.pages_found.clear()
        times = []
        func_time = time()

        while pages_to_scan:
            start_url = pages_to_scan.popleft()

            if start_url in self.pages_scanned:
                continue

            scan_time = time()
            headers = {
                "User-Agent": choice(USER_AGENTS),
            }
            print("scanning:", start_url)

            try:
                response = requests.get(start_url, headers=headers)
                response.raise_for_status()
            except (HTTPError, ConnectionError) as error:
                print(f"exception: {error}")
                continue

            final_url = start_url if not response.history else clean_tags(response.url)
            if final_url in self.pages_scanned:
                continue
            self.pages_scanned.update({start_url, final_url})

            if start_url != final_url:
                print("redirected to:", final_url)
                if get_pattern(start_url, False) != get_pattern(final_url, False):
                    print("skipped:", final_url)
                    continue

            html = response.text
            template = get_template(final_url)
            links, _ = search_for_hrefs(
                final_url, template, html, self.other_domains, self.nesting_limit, self.ignore_list
            )

            self.pages_found.update(links)
            unique_links = links - self.pages_scanned - set(pages_to_scan)
            pages_to_scan.extend(unique_links)
            times.append(time() - scan_time)

            if self.time_limit and time() - func_time >= self.time_limit:
                print("\nreached time limit.")
                break
            elif self.scanned_limit and len(self.pages_scanned) >= self.scanned_limit:
                print("\nreached scanned pages limit.")
                break
            elif self.found_limit and len(self.pages_found) >= self.found_limit:
                print("\nreached found pages limit.")
                break

        total_time = time() - func_time
        performance = performance_report(total_time, times)
        print("\ndone by", performance["total"], "secs.")

        if "mean" in performance:
            print("\nmean time per page:", performance["mean"], "secs.")
            print("max time per page:", performance["max"], "secs.")
            print("min time per page:", performance["min"], "secs.")

        print("\nscanned:", len(self.pages_scanned))
        print("found:", len(self.pages_found))

        return performance, list(self.pages_scanned), sorted(self.pages_found)


def performance_report(total_time: float, times: list) -> dict:
    """
    Makes performance report.
    """

    report = {
        "total": round(total_time, 2)
    }
    if times:
        report["mean"] = round(mean(times), 2)
        report["max"] = round(max(times), 2)
        report["min"] = round(min(times), 2)

    return report


class AsyncParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
                    tasks = [self.scan_page(session, link) for link in unique_links]
                    await asyncio.gather(*tasks)

        except aiohttp.client.ClientResponseError as e:
            print(f"exception: {e.status} {e.message} {start_url}")
