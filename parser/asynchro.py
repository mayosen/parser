import asyncio
import aiohttp
from time import time
from statistics import mean
from random import choice

from main import search_for_hrefs, get_template, write_report, USER_AGENTS


async def request_and_scan_page(session: aiohttp.ClientSession,
                                url: str, subdomains=True, nesting_limit=0):
    headers = {
        "User-Agent": choice(USER_AGENTS)
    }

    async with session.get(url, headers=headers) as response:
        print("scanning:", url)
        response.raise_for_status()
        page = await response.text()

    template = get_template(url)
    clean_links, _ = search_for_hrefs(template, page, subdomains, nesting_limit)
    return set(clean_links)


async def run_for_pages(first_url: str, subdomains=True, nesting_limit=0,
                        time_limit=0, scanned_limit=0, found_limit=0):
    pages_to_scan = asyncio.Queue()
    pages_to_scan.put_nowait(first_url)

    pages_scanned = set()
    pages_found = set()

    times = []
    func_time = time()

    async with aiohttp.ClientSession() as session:
        while not pages_to_scan.empty():
            scan_time = time()

            url = await pages_to_scan.get()
            # url = pages_to_scan.get_nowait()
            # Альтернативный способ. Разницы в скорости не замечено

            if url in pages_scanned:
                pages_to_scan.task_done()
                continue

            links = await request_and_scan_page(
                session, url, subdomains, nesting_limit)

            pages_found.update(links)
            pages_scanned.add(url)
            unique_links = set(links) - pages_scanned
            for item in unique_links:
                pages_to_scan.put_nowait(item)

            times.append(time() - scan_time)
            pages_to_scan.task_done()

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


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    url = "https://www.google.com/"

    _, scanned, found = asyncio.run(
        run_for_pages(
            url, subdomains=True, nesting_limit=3,
            time_limit=0, scanned_limit=15, found_limit=0)
    )
    write_report(
        url, "async",
        scanned=len(scanned),
        found=len(found),
        endpoints=found
    )
