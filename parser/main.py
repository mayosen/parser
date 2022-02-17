import requests
from random import choice
from bs4 import BeautifulSoup
from collections import deque
import json


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
    dot_position = url.find(".")
    slash_position = url.find("/", dot_position)
    main_url = url[:slash_position]
    return main_url


def get_adress(main_url: str, full=False):
    protocol = 8  # len("https://")

    if not full:
        dot_position = main_url.rfind(".")
        return main_url[protocol:dot_position]
    else:
        return main_url[8:]


def process_link(main_url: str, link: str):
    if "?" in link:
        link = link[:link.rfind("?")]

    if get_adress(main_url, True) not in link:
        if link.startswith("/") or link.startswith("#"):
            if link == "/" or link == "#":
                link = main_url
            else:
                link = main_url + link
        else:
            return None
    elif not link.startswith("https://"):
        return None

    if "#" in link:
        link = link[:link.rfind("#")]

    return link


def search_for_hrefs(main_url, page: str):
    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    cleaned_links = []

    for link in links:
        processed_link = process_link(main_url, link['href'])

        if processed_link:
            cleaned_links.append(processed_link)

    dirt_links = [link['href'] for link in links]

    return dirt_links, cleaned_links


def run_for_pages():
    pass


def scan_page(url: str):
    main_url = get_main_url(url)
    page = request_for_page(url)
    print("scanning:", main_url)
    dirt_links, links_on_page = search_for_hrefs(main_url, page)
    return main_url, sorted(set(links_on_page))


def form_report(url: str, scanned_pages: int, found_pages: int, pages: list):
    return {
        "url": url,
        "scanned_pages": scanned_pages,
        "found_pages": found_pages,
        "pages": pages
    }


def write_report(main_url, links: list):
    # scanned_pages = 1
    with open("samples/" + get_adress(main_url) + ".json", "w") as file:
        # Стоит получше продумать структуру
        report = form_report(url, 1, len(links), links),
        json.dump(report, file, indent=4)


if __name__ == "__main__":
    # url = "https://dvmn.org/modules/"
    # url = "https://edu.avosetrov.ru/"
    # url = "https://gljewelry.com/about/"
    url = "https://spinit.dev/"

    # url = "https://ru.wikipedia.org/wiki/Переменная_звезда"
    # url = "https://docs-python.ru/tutorial/operatsii-tekstovymi-strokami-str-python/metod-str-rfind/"
    # url = "https://stackoverflow.com/questions/5815747/beautifulsoup-getting-href/"

    main_url, links = scan_page(url)
    # write_report(main_url, list(links))


