from collections import deque
from random import choice
from statistics import mean
from time import time

import requests
from requests.exceptions import HTTPError, ConnectionError

from consts import USER_AGENTS
from scanner import get_pattern, get_template, search_for_hrefs, clean_tags, split_endpoints


def request_for_page(url: str) -> tuple[str, str]:
    """
    Requests for a page.
    """

    headers = {
        "User-Agent": choice(USER_AGENTS),
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    if response.history:
        url = clean_tags(response.url)

    return url, response.text


def scan_page(start_url: str, other_domains=True, nesting_limit=0, ignore_list=None) -> tuple[set, set]:
    """
    Finds links on the page.
    """

    print("scanning:", start_url)
    final_url, page = request_for_page(start_url)

    if start_url != final_url:
        print("redirected to:", final_url)
    if get_pattern(start_url, False) != get_pattern(final_url, False):
        return set(), set()

    template = get_template(final_url)
    clean_links, dirt_links = search_for_hrefs(final_url, template, page, other_domains, nesting_limit, ignore_list)

    return clean_links, dirt_links


def run_for_pages(
        first_url: str,
        other_domains=True,
        nesting_limit=0,
        time_limit=0,
        scanned_limit=0,
        found_limit=0,
        ignore_list: list[str] = None,
        params: dict = None,
) -> tuple[dict, list, list]:
    """
    Makes a pass through all the pages found and scans it.
    """

    pages_to_scan = deque()
    pages_to_scan.append(first_url)
    pages_scanned = set()
    pages_found = set()
    times = []
    func_time = time()

    if params:
        other_domains = params.get("other_domains", True)
        nesting_limit = params.get("nesting_limit", 0)
        time_limit = params.get("time_limit", 0)
        scanned_limit = params.get("scanned_limit", 0)
        found_limit = params.get("found_limit", 0)
        ignore_list = params.get("ignore_list", None)
    if ignore_list:
        ignore_list = [split_endpoints(ignore_sample) for ignore_sample in ignore_list]

    while pages_to_scan:
        url = pages_to_scan.popleft()
        if url in pages_scanned:
            continue

        scan_time = time()
        try:
            links, _ = scan_page(url, other_domains, nesting_limit, ignore_list)
        except (HTTPError, ConnectionError) as error:
            print(f"exception: {error}")
            continue

        pages_found.update(links)
        pages_scanned.add(url)
        unique_links = links - pages_scanned - set(pages_to_scan)
        pages_to_scan.extend(unique_links)
        times.append(time() - scan_time)

        if time_limit and time() - func_time >= time_limit:
            print("\nreached time limit.")
            break
        elif scanned_limit and len(pages_scanned) >= scanned_limit:
            print("\nreached scanned pages limit.")
            break
        elif found_limit and len(pages_found) >= found_limit:
            print("\nreached found pages limit.")
            break

    total_time = time() - func_time
    performance = performance_report(total_time, times)
    print("\ndone by", performance["total"], "secs.")

    if "mean" in performance:
        print("\nmean time per page:", performance["mean"], "secs.")
        print("max time per page:", performance["max"], "secs.")
        print("min time per page:", performance["min"], "secs.")

    print("\nscanned:", len(pages_scanned))
    print("found:", len(pages_found))

    return performance, list(pages_scanned), sorted(pages_found)


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
