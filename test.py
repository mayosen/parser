import json
import asyncio
from os import listdir

from main import scan_page, write_report, run_for_pages
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
            write_report(
                url, "t_clean",
                scanned=1,
                found=len(links),
                endpoints=sorted(links),
            )
            write_report(
                url, "t_dirt",
                scanned=1,
                found=len(dirt_links),
                endpoints=sorted(dirt_links)
            )
            raise FailedTest(
                f"url: {url} expected: {sample['found']} "
                f"vs scanned: {len(links)}")
    else:
        print("successfully tested.")


def test_report(url: str, postfix: str, times: dict,
                scanned: list, found: list):
    write_report(
        url, postfix,
        scanned=len(scanned),
        found=len(found),
        times=times,
        endpoints=found,
    )


def test_sync(url: str):
    print("scanning synchronously.")

    print("\nscanning with time limit.\n")
    times, scanned, found = run_for_pages(url, time_limit=5)
    test_report(url, "t_time_sync", times, scanned, found)

    print("\nscanning with scanned limit.\n")
    times, scanned, found = run_for_pages(url, scanned_limit=15)
    test_report(url, "t_scanned_sync", times, scanned, found)

    print("\nscanning with found limit.\n")
    times, scanned, found = run_for_pages(url, found_limit=250)
    test_report(url, "t_found_sync", times, scanned, found)


def test_async(url: str):
    print("scanning asynchronously.")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("\nscanning with time limit.\n")
    times, scanned, found = asyncio.run(run_async(url, time_limit=5))
    test_report(url, "t_time_async", times, scanned, found)

    print("\nscanning with scanned limit.\n")
    times, scanned, found = asyncio.run(run_async(url, scanned_limit=15))
    test_report(url, "t_scanned_async", times, scanned, found)

    print("\nscanning with found limit.\n")
    times, scanned, found = asyncio.run(run_async(url, found_limit=250))
    test_report(url, "t_found_async", times, scanned, found)


if __name__ == "__main__":
    samples = read_all_samples()
    test_scan_page(samples)

    # url = "https://www.google.com/"
    # test_sync(url)
    # test_async(url)
