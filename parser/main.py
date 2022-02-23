from pprint import pprint

import requests
import json
from time import time
from random import choice
from collections import deque
from statistics import mean
from bs4 import BeautifulSoup


USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) "
        "Gecko/20100101 Firefox/94.0"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) "
        "Gecko/20100101 Firefox/95.0"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36"),
]


def request_for_page(url: str):
    headers = {
        "User-Agent": choice(USER_AGENTS)
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def get_main_url(url: str):
    first_dot = url.find(".")
    if "/" in url[first_dot:]:
        url = url[:url.find("/", first_dot)]

    return url


def get_main_domain(url: str):
    url = url[:url.rfind(".")]

    if "." in url:
        url = url[url.rfind(".") + 1:]
    else:
        url = url[url.rfind("/") + 1:]

    return url


def is_other_site(url: str):
    other = False

    if "." in url:
        if url.endswith(".html"):
            url = url[:-5]
        elif url.endswith(".htm"):
            url = url[:-4]

        if "." in url:
            other = True

    return other


def form_report(url: str, scanned_pages: int, found_pages: int, pages: list):
    return {
        "url": url,
        "scanned_pages": scanned_pages,
        "found_pages": found_pages,
        "pages": pages
    }


def write_report(url: str, scanned: int, links: list, postfix=""):
    main_domain = get_main_domain(url)

    if not postfix:
        file_name = "samples/" + main_domain + ".json"
    else:
        file_name = "temp/_" + main_domain + "_" + postfix + ".json"

    with open(file_name, "w") as file:
        report = form_report(url, scanned, len(links), links),
        json.dump(report, file, indent=4)


def has_subdomains(link: str):
    clean_link = link[link.find("/") + 2:]
    subdomains = clean_link[:clean_link.find("/")].count(".") - 1
    return subdomains > 0


def count_nesting(link: str):
    clean_link = link[link.find("/") + 2:]
    dots = clean_link[:clean_link.rfind("/") + 1].count(".") - 1
    slashes = clean_link.count("/")
    if not link[link.rfind("/") + 1:]:
        slashes -= 1

    return dots + slashes


def get_pattern(main_url: str):
    return get_main_domain(main_url) + main_url[main_url.rfind("."):]


def process_link(main_url: str, link: str, subdomains=True, nesting_limit=0):
    if "?" in link:
        link = link[:link.find("?")]

    pattern = get_pattern(main_url)

    if pattern not in link:
        if link.startswith("/") or link.startswith("#"):
            if link == "/" or link == "#":
                link = main_url + "/"
            elif is_other_site(link):
                return None
            else:
                link = main_url + link
        else:
            return None
    elif link.startswith("//"):
        if "." in link[link.find(pattern) + len(pattern):]:
            return None

        protocol = main_url[:main_url.find("/") + 2]
        link = protocol + link[2:]
    elif not (link.startswith("https://") or link.startswith("http://")):
        return None
    elif not link.startswith(main_url):
        pattern_position = link.find(pattern)
        if link[pattern_position - 1] != ".":
            return None

    if "&" in link:
        link = link[:link.find("&")]
        link = link[:link.rfind("/") + 1]

    if "=" in link:
        link = link[:link.find("=")]
        link = link[:link.rfind("/") + 1]

    if "#" in link:
        link = link[:link.rfind("#")]

    if link == main_url:
        link += "/"

    if not subdomains and has_subdomains(link):
        return None

    if nesting_limit and count_nesting(link) > nesting_limit:
        return None

    return link


def search_for_hrefs(
        main_url: str, page: str, subdomains=True, nesting_limit=0):
    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    clean_links = []

    for link in links:
        processed_link = process_link(
            main_url, link['href'], subdomains, nesting_limit)

        if processed_link:
            clean_links.append(processed_link)

    dirt_links = [link['href'] for link in links]

    return set(clean_links), set(dirt_links)


def scan_page(url: str, subdomains=True, nesting_limit=0):
    print("scanning:", url)
    page = request_for_page(url)
    main_url = get_main_url(url)
    clean_links, dirt_links = search_for_hrefs(
        main_url, page, subdomains, nesting_limit)
    return clean_links, dirt_links


def run_for_pages(first_url: str, subdomains=True, nesting_limit=0,
                  time_limit=0, scanned_limit=0, found_limit=0):
    pages_to_scan = deque()
    pages_to_scan.append(first_url)

    pages_scanned = set()
    pages_found = set()

    times = []
    func_time = time()

    while pages_to_scan:
        url = pages_to_scan.popleft()

        if url in pages_scanned:
            continue

        scan_time = time()
        links, _ = scan_page(url, subdomains, nesting_limit)
        pages_found.update(links)
        pages_scanned.add(url)
        unique_links = set(links) - pages_scanned - set(pages_to_scan)
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

    if times:
        print(f"\ndone by {time() - func_time:.2f} secs.\n")
        print(f"scanned: {len(pages_scanned)}")
        print(f"found: {len(pages_found)}\n")
        print(f"mean time per page: {mean(times):.2f}")
        print(f"max time per page: {max(times):.2f}")
        print(f"min time per page: {min(times):.2f}")

        times.append(time() - func_time)

    return times, pages_scanned, sorted(pages_found)


def build_tree(init_links: list):
    links = []

    for link in init_links:
        links.append(link[link.find("//") + 2:].rstrip("/"))

    sequences = []

    for link in links:
        if "/" in link:
            domains = link.split("/", maxsplit=1)
            dots = domains[0].split(".")[:-2][::-1]
            slashed = domains[1].split("/")
            items = dots + slashed
        else:
            items = link.split(".")[:-1][::-1]

        sequences.append(items)

    tree = {}
    for group in sequences:
        tree = merge_branch(tree, group)

    return tree


def merge_branch(tree: dict, branch: list):
    if len(branch) == 1:
        return {branch[0]: None}

    key = branch.pop(0)

    if key not in tree:
        tree[key] = merge_branch({}, branch)
    elif tree[key] is None:
        tree[key] = merge_branch({}, branch)
    else:
        temp = merge_branch(tree[key], branch)
        tree[key].update(temp)

    return tree


if __name__ == "__main__":
    urls = [
        "https://edu.avosetrov.ru/",
        "http://www.avosetrov.ru/",
        "https://dvmn.org/modules/",
        "https://gljewelry.com/about/",
        "https://www.google.ru/",
        "https://www.google.com/",
        "https://spinit.dev/",
        "https://vk.com/",
        "https://www.wikipedia.org/",
        "https://www.coursera.org/",
        "https://www.ratatype.com/",
    ]

    url = urls[5]
    #
    # links, _ = scan_page(url, 1)
    # write_report(url, 1, sorted(links), "limit_2")
    #
    _, scanned, found = run_for_pages(
        url, nesting_limit=3, subdomains=True,
        time_limit=0, scanned_limit=0, found_limit=50)
    write_report(url, len(scanned), found, "sync")

    tree = build_tree(found)
    pprint(tree)
    write_report(url, 0, tree, "ing")

