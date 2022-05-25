from argparse import ArgumentParser

from saver import load_config


def parse_args() -> tuple[str, dict, bool]:
    """
    Loads command-line arguments.
    """

    parser = ArgumentParser()
    parser.add_argument("site", type=str, help="")
    parser.add_argument("-c", "--config", type=str, default=None, help="Load config from JSON")

    parser.add_argument("-n", "--nesting", type=int, default=0, help="Endpoints nesting limit")
    parser.add_argument("-t", "--time", type=int, default=0, help="Runtime limit")
    parser.add_argument("-s", "--scanned", type=int, default=0, help="Number of scanned pages limit")
    parser.add_argument("-f", "--found", type=int, default=0, help="Number of found pages limit")
    parser.add_argument("-i", "--ignore", type=str, default="", nargs="*", help="List of forbidden endpoints")

    parser.add_argument("-others", action="store_false", help="Forbid other domains")
    parser.add_argument("-sync", action="store_true", help="Run requests synchronously")

    args = parser.parse_args()

    if args.config:
        params = load_config(args.config)
    else:
        params = dict(
            other_domains=args.others,
            nesting_limit=args.nesting,
            time_limit=args.time,
            scanned_limit=args.scanned,
            found_limit=args.found,
            ignore_list=args.ignore,
        )

    return args.site, params, args.sync
