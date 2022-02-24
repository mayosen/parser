import json
import asyncio
from os import listdir
from statistics import mean

from main import scan_page, write_report, run_for_pages
from asynchro import run_for_pages as run_async


class BrokenScanPage(Exception):
    pass


def read_sample(filename: str):
    with open(filename, "r") as file:
        report = json.load(file)

    return {
        "url": report["url"],
        "scanned": report["scanned"],
        "found": report["found"],
    }


def read_all_samples():
    sample_files = listdir("samples/")
    samples = []

    for sample_name in sample_files:
        sample = read_sample("samples/" + sample_name)
        samples.append(sample)

    return samples


def test_parser(samples: list):
    print("started testing.")

    for sample in samples:
        url = sample["url"]
        links, dirt_links = scan_page(url)

        if len(links) != sample["found"]:
            write_report(url, "t_clean",
                         scanned=1,
                         found=len(links),
                         endpoints=sorted(links),
                         )
            write_report(url, "t_dirt",
                         scanned=1,
                         found=len(dirt_links),
                         endpoints=sorted(dirt_links)
                         )
            raise BrokenScanPage(
                f"url: {url} expected: {sample['found']} "
                f"vs scanned: {len(links)}")
    else:
        print("successfully tested.")


def test_sync(url: str):
    times, scanned, found = run_for_pages(url, time_limit=5)
    total = times.pop()
    write_report(
        url, "t_async_time",
        total_time=round(total, 2),
        mean_time=round(mean(times), 2),
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
    )

    times, scanned, found = run_for_pages(url, scanned_limit=15)
    total = times.pop()
    write_report(
        url, "t_async_scanned",
        total_time=round(total, 2),
        mean_time=round(mean(times), 2),
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
    )

    times, scanned, found = run_for_pages(url, found_limit=250)
    total = times.pop()
    write_report(
        url, "t_async_found",
        total_time=round(total, 2),
        mean_time=round(mean(times), 2),
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
    )


def test_async(url: str):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    times, scanned, found = asyncio.run(run_async(url, time_limit=5))
    total = times.pop()
    write_report(
        url, "t_sync_time",
        total_time=round(total, 2),
        mean_time=round(mean(times), 2),
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
    )

    times, scanned, found = asyncio.run(run_async(url, scanned_limit=15))
    total = times.pop()
    write_report(
        url, "t_sync_scanned",
        total_time=round(total, 2),
        mean_time=round(mean(times), 2),
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
    )

    times, scanned, found = asyncio.run(run_async(url, found_limit=250))
    total = times.pop()
    write_report(
        url, "t_sync_found",
        total_time=round(total, 2),
        mean_time=round(mean(times), 2),
        scanned=len(scanned),
        found=len(found),
        endpoints=found,
    )


TESTING_SITES = [
    "https://edu.avosetrov.ru/",
    "https://dvmn.org/modules/",
    "https://gljewelry.com/about/",
    "https://www.google.ru/",
    "https://spinit.dev/",
    "https://vk.com/",
]


def write_tests(urls: list):
    for url in urls:
        links, _ = scan_page(url)
        write_report(
            url,
            scanned=1,
            found=len(links),
            endpoints=sorted(links),
        )


if __name__ == "__main__":
    samples = read_all_samples()
    test_parser(samples)

    # url = "https://www.google.com/"
    # test_sync(url)
    # test_async(url)
