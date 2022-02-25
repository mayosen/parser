import requests
import json
from time import time
from random import choice
from collections import deque
from statistics import mean
from bs4 import BeautifulSoup

from pprint import pprint


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


def get_template(url: str):
    """Returns a template for creating links by adding endpoints.

    'https://gljewelry.com/about/' -> 'https://gljewelry.com'
    """

    first_dot = url.find(".")
    if "/" in url[first_dot:]:
        url = url[:url.find("/", first_dot)]

    return url


def get_pattern(url: str, full=True):
    """Returns a top- and a second-level or only top-level domain parts.

    'https://www.google.ru/services/' -> 'google.ru' or 'google'
    """

    if url.endswith((".html", ".htm")):
        url = url[:url.rfind(".htm")]

    url = url[url.find("//") + 2:]

    if "/" in url:
        url = url[:url.find("/")]

    cutten = url[:url.rfind(".")]

    if "." in cutten:
        next_dot = cutten.rfind(".")
        url = url[next_dot + 1:]

    if not full:
        url =  url[:url.rfind(".")]

    return url


def is_other_site(url: str):
    """Checks if href like '/link' is other site.

    '/catalog/43' -> False
    '/catalog/ring.html' -> False
    '/wikipedia.org/' -> True
    """

    url = url.rstrip(".html").rstrip("htm")

    return "." in url


def has_subdomains(link: str):
    """Checks if site has subdomains.

    https://google.com/ -> False
    https://www.google.com/ -> True
    """

    link = link[link.find("/") + 2:]
    subdomains = link[:link.find("/")].count(".") - 1
    return subdomains > 0


def count_nesting(link: str):
    """Returns a number of nesting by '/' on sites."""

    link = link[link.find("/") + 2:]

    slashes = link.count("/")
    if not link[link.rfind("/") + 1:]:
        slashes -= 1

    return slashes


def process_link(template: str, link: str, subdomains=True, nesting_limit=0):
    """Returns cleaned of tags link to the site or None if link is invalid."""

    if "?" in link:
        link = link[:link.find("?")]

    pattern = get_pattern(template)

    if pattern not in link:
        if link.startswith("#"):
            link = template + "/"
        elif link.startswith("/"):
            if link == "/":
                link = template + "/"
            elif is_other_site(link):
                return None
            else:
                link = template + link
        else:
            return None
    elif link.startswith("//"):
        if "." in link[link.find(pattern) + len(pattern):]:
            return None
        protocol = template[:template.find("/") + 2]
        link = protocol + link[2:]
    elif not link.startswith(("https://", "http://")):
        return None
    elif not link.startswith(template):
        pattern_position = link.find(pattern)
        if link[pattern_position - 1] != ".":
            return None

    if "#" in link:
        link = link[:link.rfind("#")]

    if "&" in link:
        link = link[:link.find("&")]

    if link == template:
        link += "/"

    if not subdomains and has_subdomains(link):
        return None

    if nesting_limit and count_nesting(link) > nesting_limit:
        return None

    return link


def search_for_hrefs(template: str, page: str,
                     subdomains=True, nesting_limit=0):
    """Parses html page for unique <a href> tags."""

    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    clean_links = []

    for link in links:
        processed_link = process_link(
            template, link['href'], subdomains, nesting_limit)

        if processed_link:
            clean_links.append(processed_link)

    dirt_links = [link['href'] for link in links]

    return set(clean_links), set(dirt_links)


def scan_page(url: str, subdomains=True, nesting_limit=0):
    """Finds urls on the page."""
    
    print("scanning:", url)
    page = request_for_page(url)
    template = get_template(url)
    clean_links, dirt_links = search_for_hrefs(
        template, page, subdomains, nesting_limit)
    return clean_links, dirt_links


def run_for_pages(first_url: str, subdomains=True, nesting_limit=0,
                  time_limit=0, scanned_limit=0, found_limit=0):
    """Makes a pass through all the links found."""
    
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
        print(f"min time per page: {min(times):.2f}\n")

        times.append(time() - func_time)

    return times, pages_scanned, sorted(pages_found)


def merge_branch(tree: dict, branch: list):
    """Merges branch as list into dictionary.

    Every element in branch is a key.
    """

    if len(branch) == 1:
        temp = {branch[0]: None}
        tree.update(temp)
        return tree

    key = branch.pop(0)

    if key not in tree or tree[key] is None:
        tree[key] = merge_branch({}, branch)
    else:
        temp = merge_branch(tree[key], branch)
        tree[key].update(temp)

    return tree


def build_tree(url: str, init_links: list):
    """Builds tree-structure from found links.

    Subdomains and endpoints are counted equally.
    """

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
            items = link.split(".")[:-2][::-1]

        if items:
            sequences.append(items)

    tree = {}

    for group in sequences:
        tree = merge_branch(tree, group)

    return {
        get_pattern(url): tree,
    }


def write_report(url: str, postfix="", **fields):
    """Writes a JSON with custom fields."""

    pattern = get_pattern(url, full=False)

    if not postfix:
        file_name = "samples/" + pattern + ".json"
    else:
        file_name = "reports/" + pattern + "_" + postfix + ".json"

    with open(file_name, "w") as file:
        report = dict(url=url, **fields)
        json.dump(report, file, indent=4)


URLS = [
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


if __name__ == "__main__":
    url = URLS[5]

    _, scanned, found = run_for_pages(
        url, subdomains=True, nesting_limit=3,
        time_limit=0, scanned_limit=10, found_limit=0)

    tree = build_tree(url, found)

    write_report(
        url, "test",
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
        tree=tree,
    )
