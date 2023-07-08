import json
from datetime import datetime
from pathlib import Path
from typing import Sequence

from yarl import URL

from parser.web import StopReason


def write_report(
    path: Path,
    start_url: str,
    found: Sequence[str],
    scanned: Sequence[str],
    reason: StopReason,
    elapsed: float,
) -> None:
    # TODO: test with expected json. How to compare JSON in Python?
    date = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename = f"{URL(start_url).host} {date}.json"

    report = {
        "start_url": start_url,
        "total_scanned": len(scanned),
        "total_found": len(found),
        "elapsed_time": round(elapsed, 2),
        "stop_reason": reason.name,
        "scanned": scanned,
        "found": found,
    }

    with open(path / filename, "w") as file:
        json.dump(report, file, indent=4)
