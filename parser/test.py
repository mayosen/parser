import json
import asyncio
from os import listdir
from statistics import mean
from main import get_main_domain, scan_page, write_report, run_for_pages
from asynchro import run_for_pages as run_async


class BrokenScanPage(Exception):
    pass


def read_sample(filename: str):
    # Пока только для 1 сканированной страницы.

    with open(filename, "r") as file:
        report = json.load(file)[0]

    return {
        "url": report["url"],
        "scanned_pages": report["scanned_pages"],
        "found_pages": report["found_pages"],
    }


def read_all_samples():
    sample_files = listdir("samples/")
    samples = []

    for sample in sample_files:
        samples.append(read_sample("samples/" + sample))

    return samples


def test_parser(samples: list):
    print("started testing.")

    for item in samples:
        url = item["url"]
        links, dirt_links = scan_page(url)
        if len(links) != item["found_pages"]:
            write_report(url, 1, links, "t_clean")
            write_report(url, 1, dirt_links, "t_dirt")
            raise BrokenScanPage(
                f"url: {url} expected: {item['found_pages']} vs scanned: {len(links)}")
    else:
        print("successfully tested.")


def form_results(url: str, times: list, scanned: int, found: int, pages: list):
    total_time = times.pop()
    times = times

    return {
        "url": url,
        "total_time": round(total_time, 2),
        "mean_time": round(mean(times), 2),
        "scanned_pages": scanned,
        "found_pages": found,
        "pages": pages,
    }


def write_results(url: str, times: list, scanned: int, links: list, postfix=""):
    main_domain = get_main_domain(url)

    file_name = "temp/t_" + main_domain + "_" + postfix + ".json"

    with open(file_name, "w") as file:
        report = form_results(url, times, scanned, len(links), links),
        json.dump(report, file, indent=4)


def test_sync(url: str):
    times, scanned, found = run_for_pages(url, time_limit=5)
    write_results(url, times, len(scanned), found, "async_time")

    times, scanned, found = run_for_pages(url, scanned_limit=15)
    write_results(url, times, len(scanned), found, "async_scanned")

    times, scanned, found = run_for_pages(url, found_limit=250)
    write_results(url, times, len(scanned), found, "async_found")


def test_async(url: str):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    times, scanned, found = asyncio.run(run_async(url, time_limit=5))
    write_results(url, times, len(scanned), found, "sync_time")

    times, scanned, found = asyncio.run(run_async(url, scanned_limit=15))
    write_results(url, times, len(scanned), found, "sync_scanned")

    times, scanned, found = asyncio.run(run_async(url, found_limit=250))
    write_results(url, times, len(scanned), found, "sync_found")


if __name__ == "__main__":
    test_parser(read_all_samples())

    url = "https://www.google.com/"
    # test_sync(url)
    # test_async(url)

