from runner import run_for_pages
from saver import write_report


def test_report(url: str, postfix: str, times: dict,scanned: list, found: list) -> None:
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


if __name__ == "__main__":
    url = "https://www.google.com/"
    test_sync(url)
