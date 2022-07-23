import logging

import misc
from parsers import SyncParser
from tree import build_tree


if __name__ == "__main__":
    logging.basicConfig(
        format=u"%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )

    parser = SyncParser(scanned_limit=1)
    url = "http://www.avosetrov.ru/"
    times, scanned, found = parser.run(url)

    tree = build_tree(url, found)

    misc.write_report(
        url,
        scanned=len(scanned),
        found=len(found),
        times=times,
        endpoints=found,
        tree=tree
    )
