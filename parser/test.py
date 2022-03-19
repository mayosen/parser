import json
import asyncio
from os import listdir
from statistics import mean

from main import scan_page, write_report, run_for_pages, examples
from asynchro import run_for_pages as run_async


class FailedTest(Exception):
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


def write_tests(urls: list):
    for url in urls:
        links, _ = scan_page(url)
        write_report(
            url, "samples/",
            scanned=1,
            found=len(links),
            endpoints=sorted(links),
        )


def test_scan_page(samples: list):
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
            raise FailedTest(
                f"url: {url} expected: {sample['found']} "
                f"vs scanned: {len(links)}")
    else:
        print("successfully tested.")


def test_report(url: str, postfix: str, total_time: float, mean_time: float,
                scanned: int, found: int, endpoints: list):
    write_report(
        url, postfix,
        total_time=total_time,
        mean_time=mean_time,
        scanned=scanned,
        found=found,
        endpoints=endpoints,
    )


def test_sync(url: str):
    print("scanning synchronously.\n")

    print(f"scanning with time limit:", url)
    times, scanned, found = run_for_pages(url, time_limit=5)
    total = times.pop()
    test_report(url, "t_time_async", round(total, 2), round(mean(times), 2),
                len(scanned), len(found), found)

    print(f"scanning with scanned limit:", url)
    times, scanned, found = run_for_pages(url, scanned_limit=15)
    total = times.pop()
    test_report(url, "t_scanned_async", round(total, 2), round(mean(times), 2),
                len(scanned), len(found), found)

    print(f"scanning with found limit:", url)
    times, scanned, found = run_for_pages(url, found_limit=250)
    total = times.pop()
    test_report(url, "t_found_async", round(total, 2), round(mean(times), 2),
                len(scanned), len(found), found)


def test_async(url: str):
    print("scanning asynchronously.\n")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print(f"scanning with time limit:", url)
    times, scanned, found = asyncio.run(run_async(url, time_limit=5))
    total = times.pop()
    test_report(url, "t_time_sync", round(total, 2), round(mean(times), 2),
                len(scanned), len(found), found)

    print(f"scanning with scanned limit:", url)
    times, scanned, found = asyncio.run(run_async(url, scanned_limit=15))
    total = times.pop()
    test_report(url, "t_scanned_sync", round(total, 2), round(mean(times), 2),
                len(scanned), len(found), found)

    print(f"scanning with found limit:", url)
    times, scanned, found = asyncio.run(run_async(url, found_limit=250))
    total = times.pop()
    test_report(url, "t_found_sync", round(total, 2), round(mean(times), 2),
                len(scanned), len(found), found)


if __name__ == "__main__":
    samples = read_all_samples()
    test_scan_page(samples)

    # url = "https://www.google.com/"
    # test_sync(url)
    # test_async(url)
