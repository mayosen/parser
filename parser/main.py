import requests
import json
from random import choice
from bs4 import BeautifulSoup
from collections import deque


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

PAGES_TO_REQUEST = deque()
PAGES_FOUND = set()


def request_for_page(url):
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


def process_link(main_url: str, link: str, other_domains: bool):
    if "?" in link:
        link = link[:link.find("?")]

    pattern = get_main_domain(main_url) + "."
    if not other_domains:
        pattern += main_url[main_url.rfind(".") + 1:]

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
    elif not link.startswith("https://"):
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

    return link


def search_for_hrefs(main_url, page: str, other_domains: bool):
    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    cleaned_links = []

    for link in links:
        processed_link = process_link(main_url, link['href'], other_domains)

        if processed_link:
            cleaned_links.append(processed_link)

    dirt_links = [link['href'] for link in links]

    return dirt_links, cleaned_links


def run_for_pages():
    pass


def scan_page(url: str, other_domains=False):
    main_url = get_main_url(url)
    page = request_for_page(url)
    print("scanning:", main_url + "/")
    dirt_links, links_on_page = search_for_hrefs(main_url, page, other_domains)
    return sorted(set(links_on_page)), dirt_links


def form_report(url: str, scanned_pages: int, found_pages: int, pages: list):
    return {
        "url": url,
        "scanned_pages": scanned_pages,
        "found_pages": found_pages,
        "pages": pages
    }


def write_report(url: str, links: list, postfix=""):
    # scanned_pages = 1

    main_domain = get_main_domain(url)
    if not postfix:
        file_name = "samples/" + main_domain + ".json"
    else:
        file_name = "temp/_" + main_domain + "_" + postfix + ".json"

    with open(file_name, "w") as file:
        # Стоит получше продумать структуру
        report = form_report(url, 1, len(links), links),
        json.dump(report, file, indent=4)


if __name__ == "__main__":
    # url = "https://dvmn.org/modules/"
    # url = "https://www.google.ru/"
    # # url = "https://spinit.dev/"
    url = "https://www.wikipedia.org/"

    main_url = get_main_url(url)
    links, dirt_links = scan_page(url)
    write_report(url, list(links), "a")
    write_report(url, dirt_links, "dirt")
