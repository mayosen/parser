import re
import requests
from bs4 import BeautifulSoup


def extern_href(href: str):
    return href.startswith("https://dvmn.org")


# site = "https://dvmn.org/"
site = "https://stackoverflow.com/questions/5815747/beautifulsoup-getting-href/"
url = site

page = requests.get(url)
assert page.status_code == 200

parsed = BeautifulSoup(page.text, 'html.parser')
# hrefs = parsed.find_all('a', href=extern_href)
hrefs = parsed.find_all('a', href=True)

links = set()

for item in hrefs:
    link = item.get('href', None)

    # TODO: Ссылки без https:// (т.е. локальные) не парсит
    print(link)
    if link and link.startswith(("https://stackoverflow.com", "stackoverflow.com")):
        links.add(link)

sorted_links = sorted(links)
print(links, sep='\n')
