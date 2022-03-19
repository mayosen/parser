import requests
from requests.exceptions import HTTPError
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
    """Requests for page taking into account bad requests and redirects."""

    headers = {
        "User-Agent": choice(USER_AGENTS)
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    if response.history:
        url = process_redirect(response.url)

    return url, response.text


def process_redirect(url: str):
    """Cleans url from tags."""

    if "?" in url:
        url = url[:url.find("?")]
    if "#" in url:
        url = url[:url.rfind("#")]
    if "&" in url:
        url = url[:url.find("&")]
    return url


def get_template(url: str):
    """Returns a template for creating links by adding endpoints.

    'https://gljewelry.com/about/' -> 'https://gljewelry.com'
    """

    first_dot = url.find(".")
    if "/" in url[first_dot:]:
        url = url[:url.find("/", first_dot)]

    return url


def get_pattern(url: str, full=True):
    """Returns a top- and a second-level domains or domains of all levels.

    'https://www.google.ru/services/' -> 'www.google.ru' or 'google.ru'
    """

    if url.endswith((".html", ".htm")):
        url = url[:url.rfind(".")]

    url = url[url.find("//") + 2:]

    if "/" in url:
        url = url[:url.find("/")]

    if "?" in url:
        url = url[:url.find("?")]

    if not full:
        clipped = url[:url.rfind(".")]
        if "." in clipped:
            next_dot = clipped.rfind(".")
            url = url[next_dot + 1:]

    return url


def is_other_site(url: str):
    """Checks if href like '/link' is other site.

    '/catalog/43' -> False
    '/catalog/ring.html' -> False
    '/wikipedia.org/' -> True
    """

    url = url.rstrip(".html").rstrip("htm")

    return "." in url


def has_subdomains(url: str):
    """Checks if site has subdomains.

    'https://google.com/' -> False
    'https://www.google.com/' -> True
    """

    url = url[url.find("/") + 2:]
    if "/" in url:
        url = url[:url.find("/")]

    subdomains = url.count(".") - 1
    return subdomains > 0


def count_nesting(url: str):
    """Returns a number of nesting by '/' on sites."""

    url = url[url.find("/") + 2:]

    slashes = url.count("/")
    if not url[url.rfind("/") + 1:]:
        slashes -= 1

    return slashes


def process_link(page_url: str, template: str, pattern: str,
                 link: str, nesting_limit=0):
    """Returns cleaned of tags link to the site or None if link is invalid."""

    if "?" in link:
        link = link[:link.find("?")]

    if link.startswith(("tel:", "mailto:")):
        return None

    if pattern not in link:
        if is_other_site(link):
            return None
        elif link.startswith("../"):
            page_url = page_url.rstrip("/")
            page_url = page_url[:page_url.rfind("/")]
            link = page_url + link.lstrip("..")
        elif link.startswith("#"):
            link = template + "/"
        elif link == "/":
            link = template + "/"
        elif link.startswith("/"):
            link = template + link
        elif "://" in link:
            # case when link opens desktop app
            # example: 'tg://resolve' - Telegram
            return None
        elif not link:
            return None
        else:
            link = template + "/" + link
    elif link.startswith("//"):
        if "." in link[link.find(pattern) + len(pattern):]:
            return None
        protocol = template[:template.find("/") + 2]
        link = protocol + link[2:]
    elif not link.startswith(("https://", "http://")):
        return None
    elif not link.startswith(template):
        pattern_position = link.find(pattern)
        symbol = link[pattern_position - 1]
        if not (symbol == "/" or symbol == "."):
            return None

    # Checking is required domain hosted on higher level domain
    # example: 'ratatape.com' and `ratatype.com.br'
    # or if topdomain is larger when required
    # example: 'github.com' and 'github.community'
    after_domain = link[link.find(pattern) + len(pattern):]
    if after_domain and after_domain[0] != "/":
        return None

    if "#" in link:
        link = link[:link.rfind("#")]

    if "&" in link:
        link = link[:link.find("&")]

    if link == template:
        link += "/"

    if nesting_limit and count_nesting(link) > nesting_limit:
        return None

    return link


def search_for_hrefs(page_url: str, template: str, page: str,
                     other_domains=True, nesting_limit=0):
    """Parses html page for unique <a href> tags."""

    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    dirt_links = [link['href'] for link in links]
    clean_links = []
    pattern = get_pattern(template, not other_domains)

    for link in dirt_links:
        processed_link = process_link(
            page_url, template, pattern, link, nesting_limit)

        if processed_link:
            clean_links.append(processed_link)

    return set(clean_links), set(dirt_links)


def scan_page(start_url: str, other_domains=True, nesting_limit=0):
    """Finds urls on the page."""

    print("scanning:", start_url)
    final_url, page = request_for_page(start_url)
    if start_url != final_url:
        print("redirected:", final_url)
    if get_pattern(start_url, False) != get_pattern(final_url, False):
        return set(), set()
    template = get_template(final_url)
    clean_links, dirt_links = search_for_hrefs(
        final_url, template, page, other_domains, nesting_limit)
    return clean_links, dirt_links


def run_for_pages(first_url: str, other_domains=True, nesting_limit=0,
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
        try:
            links, _ = scan_page(url, other_domains, nesting_limit)
        except HTTPError as error:
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


def build_tree(url: str, found_links: list):
    """Builds tree-structure from found links.

    Subdomains and endpoints are counted equally.
    """

    links = []

    for link in found_links:
        links.append(link[link.find("//") + 2:].rstrip("/"))

    sequences = []

    for link in links:
        if "/" in link:
            domains = link.split("/", maxsplit=1)
            dots = domains[0].split(".")[:-2][::-1]
            slashes = domains[1].split("/")
            items = dots + slashes
        else:
            items = link.split(".")[:-2][::-1]

        if items:
            sequences.append(items)

    tree = {}

    for group in sequences:
        tree = merge_branch(tree, group)

    return {
        get_pattern(url, full=False): tree,
    }


def write_report(url: str, name="", **fields):
    """Writes a JSON with custom fields."""

    pattern = get_pattern(url, full=True)
    pattern = pattern[:pattern.rfind(".")]

    if name.startswith("samples/"):
        file_name = "samples/" + pattern + ".json"
    elif not name:
        file_name = "reports/" + pattern + ".json"
    else:
        file_name = "reports/" + pattern + "_" + name + ".json"

    with open(file_name, "w") as file:
        report = dict(url=url, **fields)
        json.dump(report, file, indent=4)


examples = [
    "https://edu.avosetrov.ru/",
    "http://www.avosetrov.ru/",
    "https://dvmn.org/modules/",
    "https://gljewelry.com/about/",
    "https://www.google.com/",
    "https://cloud.google.com/",
    "https://dev.vk.com/",
    "https://www.coursera.org/",
    "https://www.ratatype.com/",
    "https://slack.com/",
    "https://github.com/",
]

if __name__ == "__main__":
    site = "https://www.google.com/"

    _, scanned, found = run_for_pages(
        site, other_domains=True, nesting_limit=0,
        time_limit=0, scanned_limit=0, found_limit=0)

    # tree = build_tree(site, found)

    write_report(
        site,
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
        # tree=tree,
    )
