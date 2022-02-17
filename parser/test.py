import json
from os import listdir
from main import scan_page


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
        if sample.startswith("_"):
            continue

        samples.append(read_sample("samples/" + sample))

    return samples


def test_parser(samples: list):
    for item in samples:
        links, _ = scan_page(item["url"])
        assert len(links) == item["found_pages"], \
            f"url: {item['url']} " \
            f"expected: {item['found_pages']} vs scanned: {len(links)} " \
            f"{links}"
    else:
        print("successfully tested.")


if __name__ == "__main__":
    test_parser(read_all_samples())

