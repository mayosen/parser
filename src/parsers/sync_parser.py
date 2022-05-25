from collections import deque
from random import choice
from time import time

import requests
from requests import HTTPError

from consts import USER_AGENTS
from parsers.base_parser import BaseParser
from saver import performance_report
from scanner import clean_tags, get_pattern, get_template, search_for_hrefs


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
