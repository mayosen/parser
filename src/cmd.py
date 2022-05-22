import argparse

from saver import load_config


def pass_args():
    """
    Loads command-line arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=str, help="")
    parser.add_argument("-c", "--config", type=str, default=None, help="Load config from JSON")
    parser.add_argument("-o", "--others", type=str, default="", help="Allow other domains")
    parser.add_argument("-n", "--nesting", type=int, default=0, help="Endpoints nesting limit")
    parser.add_argument("-t", "--time", type=int, default=0, help="Runtime limit")
    parser.add_argument("-s", "--scanned", type=int, default=0, help="Number of scanned pages limit")
    parser.add_argument("-f", "--found", type=int, default=0, help="Number of found pages limit")
    parser.add_argument("-i", "--ignore", type=str, default="", nargs="*", help="List of forbidden endpoints")

    args = parser.parse_args()
    site = args.site

    if args.others and args.others.lower() == "false":
        args.others = False
    else:
        args.others = True

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

    return site, params
