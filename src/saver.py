import json

from scanner import get_pattern


def write_report(url: str, postfix="", **fields) -> None:
    """
    Writes a JSON with custom fields.
    """

    pattern = get_pattern(url, full=True)
    pattern = pattern[:pattern.rfind(".")]

    if postfix.startswith("tests/scanner/"):
        file_name = "tests/scanner/" + pattern + ".json"
    elif not postfix:
        file_name = "../reports/" + pattern + ".json"
    else:
        file_name = "../reports/" + pattern + "_" + postfix + ".json"

    with open(file_name, "w") as file:
        report = dict(url=url, **fields)
        json.dump(report, file, indent=4)


def load_config(file_name: str) -> dict:
    """
    Loads config from JSON.
    """

    with open(file_name, "r") as file:
        config = json.load(file)

    return config
