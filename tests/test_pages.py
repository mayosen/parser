from yarl import URL

from parser.pages import Host, normalize_url, search_for_urls, scan_page


class TestNormalizeUrl:
    @staticmethod
    def with_base(base_url: str):
        base = URL(base_url)
        base_host = Host(base.host)

        def wrapper(url: str) -> str | None:
            normalized = normalize_url(base, base_host, url)
            return str(normalized) if normalized else None

        return wrapper

    def test_absolute(self):
        test = self.with_base("https://dvmn.org")
        assert test("https://dvmn.org") == "https://dvmn.org"
        assert test("https://dvmn.org/payments_api/item/273/tinkoff/") == "https://dvmn.org/payments_api/item/273/tinkoff/"

    def test_relative(self):
        test = self.with_base("https://dvmn.org")
        assert test("#") == "https://dvmn.org"
        assert test("/contacts/") == "https://dvmn.org/contacts/"
        assert test("/payments_api/item/109/tinkoff/") == "https://dvmn.org/payments_api/item/109/tinkoff/"

    def test_query_params(self):
        test = self.with_base("https://dvmn.org")
        assert test("https://dvmn.org/signin/?next=/modules/") == "https://dvmn.org/signin/"

        test = self.with_base("https://www.google.ru")
        assert test("/advanced_search?hl=ru&fg=1") == "https://www.google.ru/advanced_search"
        assert test("/history/privacyadvisor/search/unauth?utm_source=googlemenu&fg=1&cctld=ru") == "https://www.google.ru/history/privacyadvisor/search/unauth"

    def test_fragment(self):
        test = self.with_base("https://dvmn.org")
        assert test("#") == "https://dvmn.org"
        assert test("/modules#id") == "https://dvmn.org/modules"

    def test_schemas(self):
        test = self.with_base("https://www.google.ru")
        assert test("https://www.google.ru") is not None
        assert test("http://www.google.ru") is not None

        assert test("tel:11221") is None
        assert test("mailto:mail@mail.com") is None
        assert test("tg://resolve?domain=bot") is None
        assert test("ftp://www.google.ru") is None

    def test_extensions(self):
        test = self.with_base("https://www.google.ru")
        assert test("https://www.google.ru/article.htm") == "https://www.google.ru/article.htm"
        assert test("https://www.google.ru/article.html") == "https://www.google.ru/article.html"

        assert test("https://www.google.ru/picture.jpg") is None
        assert test("https://www.google.ru/document.pdf") is None


class TestHost:
    def test_equals(self):
        assert Host("google.ru") == Host("google.ru")
        assert Host("www.google.ru") == Host("www.google.ru")

        assert Host("www.google.ru") != Host("google.ru")
        assert Host("google.ru") != Host("www.google.ru")

    def test_equals_top_level(self):
        assert Host("google.ru") == Host("google.ru", top_level=True)
        assert Host("google.ru", top_level=True) == Host("google.ru", top_level=True)
        assert Host("www.google.ru", top_level=True) == Host("google.ru")

        assert Host("www.google.ru") != Host("google.ru", top_level=True)
        assert Host("google.ru", top_level=True) != Host("www.google.ru")

    def test_contains(self):
        assert Host("google.ru") in Host("google.ru")
        assert Host("www.google.ru") in Host("www.google.ru")
        assert Host("google.ru") in Host("www.google.ru")

        assert Host("www.google.ru") not in Host("google.ru")
        assert Host("www.google.com") not in Host("www.google.com.br")

    def test_contains_top_level(self):
        assert Host("www.google.ru", top_level=True) in Host("google.ru")
        assert Host("www.google.ru", top_level=True) in Host("www.google.ru")


def html_with_body(body: str) -> str:
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>Title</title>
        </head>
        <body>
            {body}
        </body>
        </html>
        """


class TestSearchForUrl:
    def test_finding_hrefs(self):
        html = html_with_body("""
              <p>Paragraph</p>
              <a>Empty link</a>
              <a href="/help">Link to help</a>
              <div>
                  <a href="#">Fragment link</a>
                  <a href="">Empty link</a>
                  <a href="/">Root link</a>
              </div>
            """)
        urls = search_for_urls(html)
        assert urls == {"", "/", "#", "/help"}

    def test_no_duplicates(self):
        html = html_with_body("""
            <a href="/help">Link</a>
            <a href="/help">Duplicate</a>
            """)
        urls = search_for_urls(html)
        assert urls == {"/help"}


class TestScanPage:
    async def test_simple(self):
        url = URL("https://example.org")
        host = Host(url.host)
        html = html_with_body("""
            <a href="/relative"></a>
            <a href="https://example.org/absolute"></a>
            <a href="https://www.google.com"></a>
            <a href="/"></a>
            """)
        urls = await scan_page(url, host, html)
        assert {str(url) for url in urls} == {
            "https://example.org/relative",
            "https://example.org/absolute",
            "https://example.org/",
        }
