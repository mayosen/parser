import sys

from cmd import parse_args
from saver import write_report
from scanner import get_pattern
from tree import build_tree

if __name__ == "__main__":
    if len(sys.argv) > 1:
        site, params, sync = parse_args()
    else:
        site = "https://www.google.com/"
        site = "http://www.avosetrov.ru/"
        params = dict()
        sync = False

    if sync:
        from parsers import SyncParser
        parser = SyncParser(**params)
    else:
        from parsers import AsyncParser
        parser = AsyncParser(**params)

    times, scanned, found = parser.run(site)

    tree = {
        get_pattern(site, full=False): build_tree(site, found),
    }

    write_report(
        site,
        postfix="async",
        scanned=len(scanned),
        found=len(found),
        times=times,
        endpoints=found,
        tree=tree,
    )
