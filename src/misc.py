import json
from datetime import datetime

from yarl import URL


class Config:
    # TODO: me
    pass


def write_report(url: str, **fields):
    """
    Writes a JSON with custom fields.
    """

    name = f"{URL(url).host}_{datetime.now().strftime('%H:%M')}.json"
    with open(name, "w") as file:
        report = dict(url=url, **fields)
        json.dump(report, file, indent=4)
