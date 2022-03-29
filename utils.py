import argparse
import json
from random import choice


SITE_SAMPLES = [
    "https://edu.avosetrov.ru/",
    "http://www.avosetrov.ru/",
    "https://dvmn.org/modules/",
    "https://gljewelry.com/about/",
    "https://www.google.com/",
    "https://cloud.google.com/",
    "https://dev.vk.com/",
    "https://www.coursera.org/",
    "https://www.ratatype.com/",
    "https://slack.com/",
    "https://github.com/",
]

USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) "
     "Gecko/20100101 Firefox/94.0"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) "
     "Gecko/20100101 Firefox/95.0"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36"),
]


def get_user_agent():
    """
    Get random user agent.
    """

    return choice(USER_AGENTS)


def load_config(file_name: str = "config.json"):
    """
    Loads config from JSON.
    """

    with open(file_name, "r") as file:
        params = json.load(file)
        config = params

    return config


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

    if args.others.lower() == "false":
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
