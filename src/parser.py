import sys

from cmd import pass_args
from runner import run_for_pages
from saver import write_report
from scanner import get_pattern
from tree import build_tree


class Parser:
    pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        site, params = pass_args()
    else:
        site = "https://www.google.com/"
        # params = utils.load_config()
        params = dict(
            scanned_limit=5
        )

    times, scanned, found = run_for_pages(site, params=params)

    tree = {
        get_pattern(site, full=False): build_tree(site, found),
    }

    write_report(
        site,
        scanned=len(scanned),
        found=len(found),
        times=times,
        endpoints=found,
        tree=tree,
    )
