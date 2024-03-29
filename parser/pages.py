import asyncio
import logging
from itertools import islice

from bs4 import BeautifulSoup
from yarl import URL

logger = logging.getLogger("parser.pages")


class Host:
    def __init__(self, host: str, top_level: bool = False):
        parts = reversed(host.split("."))
        limit = 2 if top_level else None
        self.parts = tuple(islice(parts, 0, limit))

    def __eq__(self, other: object):
        if not isinstance(other, Host):
            raise NotImplementedError
        return self.parts == other.parts

    def __contains__(self, other: "Host"):
        return self.parts[: len(other.parts)] == other.parts

    def __str__(self):
        return ".".join(reversed(self.parts))

    def __repr__(self):
        return f"Host({self})"


def search_for_urls(html: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    tags = soup.find_all("a", href=True)
    raw_urls = set(link["href"] for link in tags)
    logger.debug("Found raw urls: %d", len(raw_urls))
    return raw_urls


def normalize_url(base: URL, base_host: Host, raw_url: str) -> URL | None:
    raw_url = raw_url.strip(" \n")
    logger.debug("Raw: %s", raw_url)
    url = URL(raw_url).with_fragment(None).with_query(None)

    if url.scheme and url.scheme not in ("http", "https"):
        logger.debug("Skip: unsupported scheme '%s'", url.scheme)
        return None

    if url.suffix and url.suffix not in (".htm", ".html"):
        logger.debug("Skip: not a web page with extension '%s'", url.suffix)
        return None

    if url.is_absolute():
        if base_host not in (host := Host(url.host)):
            logger.debug("Skip: host '%s' not belongs to base '%s'", host, base_host)
            return None
        if not url.scheme:
            url = url.with_scheme(base.scheme)
    else:
        url = base.join(url)

    logger.debug("Clean: %s", url)
    return url


async def scan_page(base: URL, base_host: Host, html: str) -> set[URL]:
    raw_urls = search_for_urls(html)
    await asyncio.sleep(0)
    clean_urls = set()

    for raw_url in raw_urls:
        if url := normalize_url(base, base_host, raw_url):
            clean_urls.add(url)
        await asyncio.sleep(0)

    return clean_urls
