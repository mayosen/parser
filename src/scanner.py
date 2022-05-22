from typing import Optional

from bs4 import BeautifulSoup


def clean_tags(url: str) -> str:
    """
    Cleans url from tags.
    """

    if "?" in url:
        url = url[:url.find("?")]
    if "#" in url:
        url = url[:url.rfind("#")]
    if "&" in url:
        url = url[:url.find("&")]

    return url


def get_template(url: str) -> str:
    """
    Returns a template for creating links by adding endpoints.

    Example: 'https://gljewelry.com/about/' -> 'https://gljewelry.com'
    """
    url = clean_tags(url)
    first_dot = url.find(".")
    if "/" in url[first_dot:]:
        url = url[:url.find("/", first_dot)]

    return url


def get_pattern(url: str, full=True) -> str:
    """
    Returns all level domains or a pair of top- and second-level domains.

    Example: 'https://www.google.ru/services/' -> 'www.google.ru' or 'google.ru'
    """

    url = get_template(url)
    url = url[url.find("//") + 2:]

    if not full:
        cropped = url[:url.rfind(".")]
        if "." in cropped:
            next_dot = cropped.rfind(".")
            url = url[next_dot + 1:]

    return url


def is_other_site(url: str) -> bool:
    """
    Checks if relative link refers to other site.

    Examples:
    '/catalog/43' -> False
    '/catalog/ring.html' -> False
    '/wikipedia.org/' -> True
    """

    url = url.removesuffix(".html").removesuffix(".htm")
    return "." in url


def has_subdomains(url: str) -> bool:
    """
    Checks if site has subdomains.

    Examples:
    'https://google.com/' -> False
    'https://www.google.com/' -> True
    """

    url = url[url.find("/") + 2:]
    if "/" in url:
        url = url[:url.find("/")]
    subdomains = url.count(".") - 1

    return subdomains > 0


def count_nesting(url: str) -> int:
    """
    Returns a value of endpoint nesting, counted by '/'.
    """

    url = url[url.find("/") + 2:]
    slashes = url.count("/")
    if url.endswith("/"):
        slashes -= 1

    return slashes


def split_endpoints(url: str) -> list:
    """
    Splits endpoints by slashes.

    Example:
    '/login' -> ['login']
    '/.../async/' -> ['...', 'async']
    """

    temp_list = url.split("/")
    filtered = list(filter(lambda item: item, temp_list))

    return filtered


def process_link(
        page_url: str, template: str, pattern: str, link: str, nesting_limit=0, ignore_list=None
) -> Optional[str]:
    """
    Returns cleaned and absolute link or None if link is invalid.
    """

    if "?" in link:
        link = link[:link.find("?")]
    if link.startswith(("tel:", "mailto:")):
        return None

    if pattern not in link:
        # If link is relative
        if is_other_site(link):
            return None
        elif link.startswith("../"):
            page_url = page_url.rstrip("/")
            page_url = page_url[:page_url.rfind("/")]
            link = page_url + link.removeprefix("..")
        elif link.startswith("#"):
            link = template + "/"
        elif link == "/":
            link = template + "/"
        elif link.startswith("/"):
            link = template + link
        elif "://" in link:
            # When link opens desktop app
            # Example: 'tg://resolve' - Telegram
            return None
        elif not link:
            return None
        else:
            link = template + "/" + link
    elif link.startswith("//"):
        protocol = template[:template.find("/") + 2]
        link = protocol + link[2:]
    elif not link.startswith(("https://", "http://")):
        return None
    elif not link.startswith(template):
        # Filter for similar domains
        # Example: 'google.com' and 'www.thinkwithgoogle.com'
        pattern_position = link.find(pattern)
        symbol = link[pattern_position - 1]
        if symbol not in ("/", "."):
            return None

    # Checking if required domain hosted on higher level domain
    # Example: 'ratatype.com' and 'ratatype.com.br'
    # or if domain is similar to required but longer
    # Example: 'github.com' and 'github.community'
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
    if ignore_list:
        prepared = link[link.find("//") + 2:]
        prepared = prepared[prepared.find("/") + 1:]
        prepared = split_endpoints(prepared)

        for ignore_sample in ignore_list:
            for endpoint, forbidden in zip(prepared, ignore_sample):
                if endpoint == forbidden:
                    return None

    return link


def search_for_hrefs(
        page_url: str, template: str, page: str, other_domains=True, nesting_limit=0, ignore_list=None,
) -> tuple[set, set]:
    """
    Parses html page for unique links.
    """

    parsed_soup = BeautifulSoup(page, "lxml")
    links = parsed_soup.find_all("a", href=True)
    dirt_links = [link['href'] for link in links]
    clean_links = []
    pattern = get_pattern(template, not other_domains)

    for link in dirt_links:
        processed_link = process_link(page_url, template, pattern, link, nesting_limit, ignore_list)
        if processed_link:
            clean_links.append(processed_link)

    return set(clean_links), set(dirt_links)
