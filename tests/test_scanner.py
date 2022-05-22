import json
from os import listdir

from runner import scan_page
from saver import write_report


class FailedTest(Exception):
    """Test failed."""


def read_sample(filename: str) -> dict:
    with open(filename, "r") as file:
        report = json.load(file)

    return {
        "url": report["url"],
        "scanned": report["scanned"],
        "found": report["found"],
    }


def read_all_samples() -> list[dict]:
    files = listdir("scanner/")
    samples = []

    for file in files:
        sample = read_sample("scanner/" + file)
        samples.append(sample)

    return samples


def write_tests(urls: list) -> None:
    for url in urls:
        links, _ = scan_page(url)
        write_report(
            url, "tests/scanner/",
            scanned=1,
            found=len(links),
            endpoints=sorted(links),
        )


def test_scan_page(samples: list) -> None:
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


if __name__ == "__main__":
    samples = read_all_samples()
    test_scan_page(samples)
