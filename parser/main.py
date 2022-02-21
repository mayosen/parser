import requests
import json
from random import choice
from bs4 import BeautifulSoup
from collections import deque
from time import time
from statistics import mean


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


def process_link(main_url: str, link: str, nesting_limit=0):
    if "?" in link:
        link = link[:link.find("?")]

    pattern = get_main_domain(main_url) + main_url[main_url.rfind("."):]

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
        protocol = main_url[:main_url.rfind("/") + 1]
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

    if nesting_limit:
        clean_link = link[link.find("/") + 2:]
        dots = clean_link[:clean_link.rfind("/") + 1].count(".") - 1
        slashes = clean_link.count("/")
        if not link[link.rfind("/") + 1:]:
            slashes -= 1

        nesting = dots + slashes

        if nesting > nesting_limit:
            return None

    return link


def search_for_hrefs(main_url: str, page: str, nesting_limit=0):
    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    clean_links = []

    for link in links:
        processed_link = process_link(main_url, link['href'], nesting_limit)

        if processed_link:
            clean_links.append(processed_link)

    dirt_links = [link['href'] for link in links]

    return set(clean_links), dirt_links


def scan_page(url: str, nesting_limit=0):
    print("scanning:", url)
    page = request_for_page(url)
    main_url = get_main_url(url)
    clean_links, dirt_links = search_for_hrefs(main_url, page, nesting_limit)
    return clean_links, dirt_links


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


def run_for_pages(first_url: str, nesting_limit=0):
    pages_to_scan = deque()
    pages_to_scan.append(first_url)

    pages_scanned = set()
    pages_found = set()

    times = []
    func_time = time()
    counter = 1

    while pages_to_scan:
        url = pages_to_scan.popleft()

        if url in pages_scanned:
            continue

        scan_time = time()
        links, _ = scan_page(url, nesting_limit)
        pages_found.update(links)
        pages_scanned.add(url)
        unique_links = set(links) - pages_scanned - set(pages_to_scan)
        pages_to_scan.extend(unique_links)

        """
        if counter % 10 == 0:
            print(f"{counter}, pages to scan left: {len(pages_to_scan)}")

            
            if time() - func_time > 10:
                print("\nreached time limit.")
                break
            
        if len(pages_found) > 500:
            print("\nreached pages limit.")
            break
        """

        if time() - func_time > 30:
            print("\nreached time limit.")
            break

        times.append(time() - scan_time)
        counter += 1

    print(f"\ndone by {time() - func_time:.2f} secs.\n")
    print(f"scanned: {len(pages_scanned)}")
    print(f"found: {len(pages_found)}\n")
    print(f"mean time per page: {mean(times):.2f}")
    print(f"max time per page: {max(times):.2f}")
    print(f"min time per page: {min(times):.2f}")

    return pages_scanned, sorted(pages_found)


if __name__ == "__main__":
    urls = [
        "https://edu.avosetrov.ru/",
        "https://dvmn.org/modules/",
        "https://gljewelry.com/about/",
        "https://www.google.ru/",
        "https://spinit.dev/",
        "https://vk.com/",
        "https://www.wikipedia.org/",
        "https://www.coursera.org/",
        "http://www.avosetrov.ru/",
    ]

    url = "https://www.ratatype.com/"

    scanned, found = run_for_pages(url)
    write_report(url, len(scanned), found, "sync")
