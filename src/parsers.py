import asyncio
from abc import abstractmethod, ABC
from collections import deque
from random import choice
from statistics import mean
from time import time
import logging

import aiohttp
import requests
from requests import HTTPError
from yarl import URL

import scantools
from consts import USER_AGENTS


class BaseParser(ABC):
    def __init__(
            self,
            subdomains: bool = True,
            nesting: int = None,
            ignore: list[str] = None,
            time_limit: int = None,
            scanned_limit: int = None,
            found_limit: int = None,
    ):
        self.subdomains = subdomains
        self.nesting = nesting
        self.ignore = scantools.IgnorePatterns(ignore) if ignore else None

        self.time_limit = time_limit
        self.scanned_limit = scanned_limit
        self.found_limit = found_limit

    @abstractmethod
    def run(self, first_url: str) -> tuple[dict, list, list]:
        """Recursively scan site"""
        raise NotImplementedError


class SyncParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, first_url: str) -> tuple[dict, list, list]:
        pages_to_scan = deque([first_url])
        scanned = set()
        found = set()
        times = []
        started = time()

        while pages_to_scan:
            url = URL(pages_to_scan.popleft())

            if str(url) in scanned:
                continue

            scan_time = time()
            headers = {"User-Agent": choice(USER_AGENTS)}
            logging.info("scanning: %s", url)
            
            try:
                response = requests.get(str(url), headers=headers)
                response.raise_for_status()

            except (HTTPError, ConnectionError) as error:
                logging.error("exception: %s", error)
                continue

            scanned.add(str(url))

            if response.history:
                logging.info("redirect: %s", url)
                host = scantools.Host(url.host)
                new_url = URL(response.url).with_query(None).with_fragment(None)
                new_host = scantools.Host(new_url.host)

                if str(new_url) in scanned:
                    logging.info("already scanned: %s", url)
                    continue

                if not host.equals(new_host):
                    logging.info("skipped, bad top domains: %s", new_url)
                    continue

                if not self.subdomains and not host.check(new_host):
                    logging.info("skipped, subdomain: %s", new_url)
                    continue

                scanned.add(str(new_url))
                url = new_url

            clean, dirt = scantools.scan_page(url, response.text, self.subdomains, self.nesting, self.ignore)
            found.update(clean)
            unique = clean - scanned - set(pages_to_scan)
            pages_to_scan.extend(unique)
            times.append(time() - scan_time)

            if self.time_limit and time() - started >= self.time_limit:
                logging.info("reached time limit")
                break
            elif self.scanned_limit and len(scanned) >= self.scanned_limit:
                logging.info("reached scanned limit")
                break
            elif self.found_limit and len(found) >= self.found_limit:
                logging.info("reached found limit")
                break

        total_time = time() - started

        performance = performance_report(total_time, times)
        print("\ndone by", performance["total"], "secs.")

        if "mean" in performance:
            print("\nmean time per page:", performance["mean"], "secs.")
            print("max time per page:", performance["max"], "secs.")
            print("min time per page:", performance["min"], "secs.")

        print("\nscanned:", len(scanned))
        print("found:", len(found))

        return performance, list(scanned), sorted(found)


# TODO: Добавлять base в список найденных и отсканированных
# TODO: Чтобы не было дубликатов с/без слешем в конце


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


"""
class AsyncParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def run(self, first_url: str) -> tuple[dict, list, list]:
        self.scanned.clear()
        self.found.clear()
        started = time()
        asyncio.run(self.main(first_url))
        times = {}
        times["total"] = round(time() - started, 2)
        times["mean"] = round(times["total"] / len(self.scanned), 2)
        return times, list(self.scanned), sorted(self.found)

    async def main(self, first_url: str):
        async with aiohttp.ClientSession() as session:
            await self.scan_page(session, first_url)

    async def scan_page(self, session: aiohttp.ClientSession, start_url: str):
        if start_url in self.scanned:
            # print("already scanned:", start_url)
            return
        headers = {
            "User-Agent": choice(USER_AGENTS),
        }

        try:
            async with session.get(start_url, headers=headers) as response:
                response.raise_for_status()
                final_url = start_url if not response.history else clean_tags(str(response.url))

                if final_url in self.scanned:
                    # print("already scanned:", final_url)
                    return

                print("scanning:", start_url)
                self.scanned.update({start_url, final_url})

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
                    final_url, template, html, self.subdomains, self.nesting, self.ignore,
                )
                self.found.update(links)
                unique_links = links - self.scanned

                if unique_links:
                    tasks = [self.scan_page(session, link) for link in unique_links]
                    await asyncio.gather(*tasks)

        except aiohttp.client.ClientResponseError as e:
            print(f"exception: {e.status} {e.message} {start_url}")
"""
