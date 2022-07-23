from bs4 import BeautifulSoup
from yarl import URL


class Host:
    def __init__(self, host: str):
        self.raw_host = host
        self.domains = host.split(".")[::-1]

    def equals(self, other: "Host", level: int = 2) -> bool:
        """Compare hosts by level."""
        return self.domains[:level] == other.domains[:level]

    def check(self, other: "Host") -> bool:
        """Check if the provided host is on another subdomain."""
        for left, right in zip(self.domains, other.domains):
            if left != right:
                return False
        return True

    def rebuild(self, level: int = 2) -> str:
        return ".".join(self.domains[:level][::-1])


class IgnorePatterns:
    def __init__(self, raw_patterns: list[str]):
        self.patterns = []
        for pattern in raw_patterns:
            filtered = list(filter(lambda item: item, pattern.split("/")))
            self.patterns.append(filtered)

    def check(self, url_parts: tuple[str]) -> bool:
        """Check if provided url parts as endpoints are forbidden by user."""
        for pattern in self.patterns:
            for part, forbidden in zip(url_parts, pattern):
                if part == forbidden:
                    return False
        return True


def process_link(
        base: URL,
        base_host: Host,
        raw_url: str,
        subdomains: bool = True,
        nesting: int = None,
        ignore: IgnorePatterns = None
) -> str | None:

    url = URL(raw_url).with_query(None).with_fragment(None)

    if url.is_absolute():
        url = url.with_scheme(url.scheme or base.scheme)  # For example: "//wikipedia.org"
        url_host = Host(url.host)
        if not base_host.equals(url_host):
            return None
        if not subdomains and not base_host.check(url_host):
            return None
    elif str(url).startswith(("mailto:", "tel:")):
        return None
    else:
        url = base.join(url)
        url_host = base_host

    if nesting:
        filtered_parts = list(filter(lambda item: item, url.parts))
        if len(filtered_parts) - 1 > nesting:
            return None

    if ignore:
        parts = url.parts[1:]
        if not ignore.check(parts):
            return None

    return str(url)


def scan_page(
        base: URL,
        html: str,
        subdomains: bool = True,
        nesting: int = None,
        ignore: IgnorePatterns = None
) -> tuple[set, set]:

    base_host = Host(base.host)
    soup = BeautifulSoup(html, "lxml")
    tags = soup.find_all("a", href=True)
    dirt_links = set(link["href"] for link in tags)
    clean_links = []

    for current_link in dirt_links:
        processed_link = process_link(base, base_host, current_link, subdomains, nesting, ignore)
        if processed_link:
            clean_links.append(processed_link)

    return set(clean_links), dirt_links
