import asyncio
import aiohttp
from time import time
from statistics import mean
from random import choice
from main import search_for_hrefs, get_main_url, write_report, USER_AGENTS


async def request_and_scan_page(session: aiohttp.ClientSession,
                                url: str, nesting_limit=0, subdomains=True):
    headers = {
        "User-Agent": choice(USER_AGENTS)
    }

    async with session.get(url, headers=headers) as response:
        print("scanning:", url)
        page = await response.text()

    main_url = get_main_url(url)
    clean_links, _ = search_for_hrefs(main_url, page, nesting_limit, subdomains)
    return set(clean_links)


async def run_for_pages(first_url: str, nesting_limit=0, subdomains=True):
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

            if url in pages_scanned:
                pages_to_scan.task_done()
                continue

            links = await request_and_scan_page(
                session, url, nesting_limit, subdomains)

            pages_found.update(links)
            pages_scanned.add(url)
            unique_links = set(links) - pages_scanned
            for item in unique_links:
                pages_to_scan.put_nowait(item)

            times.append(time() - scan_time)
            pages_to_scan.task_done()

            """
            if len(pages_scanned) % 10 == 0:
                print(f"scanned: {len(pages_scanned)}, left to scan: {pages_to_scan.qsize()}")
            
            if len(pages_found) > 500:
                print("\nreached pages limit.")
                break
            """

            if time() - func_time > 10:
                print("\nreached time limit.")
                break

    print(f"\ndone by {time() - func_time:.2f} secs.\n")
    print(f"scanned: {len(pages_scanned)}")
    print(f"found: {len(pages_found)}\n")
    print(f"mean time per page: {mean(times):.2f}")
    print(f"max time per page: {max(times):.2f}")
    print(f"min time per page: {min(times):.2f}")

    return pages_scanned, sorted(pages_found)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    url = "https://www.google.com/"

    scanned, found = asyncio.run(run_for_pages(url, 2))
    write_report(url, len(scanned), found, "async")
