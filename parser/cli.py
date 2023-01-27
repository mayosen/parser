import asyncio
import logging
import time
from pathlib import Path

import click
from aiohttp import ClientTimeout
from yarl import URL

from parser import web
from parser.reports import write_report


def parse_url(
    url: str,
    timeout: float | None,
    max_scanned: int | None,
    max_found: int | None,
    request_timeout: ClientTimeout,
    workers_number: int,
    check_interval: float,
) -> tuple[set[URL], set[URL], web.StopReason, float]:
    started = time.monotonic()
    result: tuple[set[URL], set[URL], web.StopReason] = asyncio.run(web.parse(
        url=url,
        timeout=timeout,
        max_scanned=max_scanned,
        max_found=max_found,
        request_timeout=request_timeout,
        workers_number=workers_number,
        check_interval=check_interval,
    ))
    found, scanned, reason = result
    elapsed = time.monotonic() - started
    return found, scanned, reason, elapsed


@click.command
@click.argument("url", type=str)
@click.option("--timeout", type=float,
              help="Total timeout for scanning. Parser doesn't guarantee what parsing will be finished "
                   "immediately after the timeout. This limit serves as a stop signal to workers.")
@click.option("--max_scanned", type=int,
              help="Limit for scanned urls. Parser doesn't guarantee what exactly 'n' urls will be scanned, "
                   "but at least 'n'. This limit serves as a stop signal to workers.")
@click.option("--max_found", type=int,
              help="Limit for found urls. Parser doesn't guarantee what exactly 'n' urls will be found, "
                   "but at least 'n'. This limit serves as a stop signal to workers.")
@click.option("--request_timeout", type=float, default=web.DEFAULT_REQUEST_TIMEOUT.total, show_default=True,
              help="Timeout for single request.")
@click.option("--workers_number", type=int, default=web.DEFAULT_WORKERS_NUMBER, show_default=True,
              help="Number of workers who scan urls concurrently.")
@click.option("--check_interval", type=float, default=web.DEFAULT_CHECK_INTERVAL, show_default=True,
              help="Interval for checking the exceeded limits (s).")
def parse(
    url: str,
    timeout: float | None,
    max_scanned: int | None,
    max_found: int | None,
    request_timeout: float,
    workers_number: int,
    check_interval: float,
) -> None:
    """Parse given URL and save results to json in current directory."""

    logging.basicConfig(
        format="%(asctime)5s.%(msecs)03d [%(levelname)s] %(name)s - %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("parser.pages").setLevel(logging.INFO)

    request_timeout = ClientTimeout(total=request_timeout)

    found, scanned, reason, elapsed = parse_url(
        url, timeout, max_scanned, max_found, request_timeout, workers_number, check_interval)

    found = sorted([str(url) for url in found])
    scanned = sorted([str(url) for url in scanned])

    write_report(Path.cwd(), url, found, scanned, reason, elapsed)


if __name__ == "__main__":
    parse()
