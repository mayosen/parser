import json
from os import listdir
from main import scan_page, write_report


def read_sample(filename: str):
    # Пока только для 1 сканированной страницы.

    with open(filename, "r") as file:
        report = json.load(file)

    return {
        "url": report[0]["url"],
        "scanned_pages": report[0]["scanned_pages"],
        "found_pages": report[0]["found_pages"],
    }


def read_all_samples():
    sample_files = listdir("samples/")
    samples = []

    for sample in sample_files:
        samples.append(read_sample("samples/" + sample))

    return samples


class BrokenScanPage(Exception):
    pass


def test_parser(samples: list):
    print("started testing.")

    for item in samples:
        url = item["url"]
        links, dirt_links = scan_page(url)
        if len(links) != item["found_pages"]:
            write_report(url, links, "clean")
            write_report(url, dirt_links, "dirt")
            raise BrokenScanPage(
                f"url: {url} expected: {item['found_pages']} vs scanned: {len(links)}")
    else:
        print("successfully tested.")


if __name__ == "__main__":
    test_parser(read_all_samples())
