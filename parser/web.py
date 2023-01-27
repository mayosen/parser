import asyncio
import logging
from enum import Enum
from typing import Coroutine, Any, TypeVar, Generic, Sized, cast

from aiohttp import ClientSession, ClientTimeout
from fake_useragent import UserAgent
from yarl import URL

from parser.pages import Host, normalize_url, scan_page

T = TypeVar("T")
REQUEST_TIMEOUT = ClientTimeout(total=10)
CHECK_INTERVAL = 0.1

user_agent = UserAgent()
module_logger = logging.getLogger("parser.web")


class StopReason(Enum):
    ALL_PROCESSED = None
    TIMEOUT = None
    FOUND_LIMIT = "found"
    SCANNED_LIMIT = "scanned"

    def __init__(self, limit_name: str | None):
        self.limit_name = limit_name


class StopScanning(Exception):
    """Notify tasks that scanning has to be finished."""

    def __init__(self, reason: StopReason):
        super().__init__()
        self.reason = reason


class UniqueQueue(Generic[T]):
    """Wrapper for asyncio.Queue receiving only unique elements."""

    def __init__(self):
        self._queue = asyncio.Queue[T]()
        self._values = set()

    def get(self) -> Coroutine[Any, Any, T]:
        return self._queue.get()

    def put_nowait(self, item: T) -> None:
        if item not in self._values:
            self._queue.put_nowait(item)
            self._values.add(item)

    def task_done(self) -> None:
        self._queue.task_done()

    def join(self) -> Coroutine[Any, Any, None]:
        return self._queue.join()

    def qsize(self) -> int:
        return self._queue.qsize()

    def __repr__(self):
        return f"<UniqueQueue size={self.qsize()}>"


async def work(name: str, session: ClientSession, queue: UniqueQueue[URL], found: set[URL], scanned: set[URL]) -> None:
    logger = module_logger.getChild(name)

    while True:
        url = await queue.get()

        try:
            host = Host(url.host)
            headers = {"User-Agent": user_agent.random}
            logger.info("Started scanning: %s", url)

            async with session.get(url, allow_redirects=False, timeout=REQUEST_TIMEOUT, headers=headers) as response:
                if response.status in (301, 302):
                    raw_redirect = response.headers["location"]
                    logger.info("Got %d redirect: %s", response.status, raw_redirect)
                    scanned.add(url)
                    found.add(url)

                    if redirect_url := normalize_url(url, host, raw_redirect):
                        queue.put_nowait(redirect_url)
                        found.add(redirect_url)
                        logger.info("Redirect added to the end of queue: %s", redirect_url)
                    else:
                        logger.info("Redirect skipped")
                    continue

                if not response.ok:
                    logger.info("Got bad response %d: %s", response.status, response.reason)

                html = await response.text()
                page_links = await scan_page(url, host, html)
                scanned.add(url)

                found_before = len(found)
                found.update(page_links)

                for link in page_links:
                    queue.put_nowait(link)

                logger.info("Found links: %d new, %d in total", len(found) - found_before, len(page_links))
                logger.debug("Current queue size is %d", queue.qsize())

        except asyncio.TimeoutError:
            logger.info("Cannot get response from %s", url)
            continue

        finally:
            queue.task_done()


async def watch_for_scanning_completion(queue: UniqueQueue[URL]) -> None:
    await queue.join()
    module_logger.info("All urls have been processed")
    raise StopScanning(StopReason.ALL_PROCESSED)


async def watch_for_numeric_limit(reason: StopReason, limit: int | None, collection: Sized) -> None:
    if limit:
        while True:
            if len(collection) >= limit:
                module_logger.info("Got %s limit", reason.limit_name)
                raise StopScanning(reason)

            await asyncio.sleep(CHECK_INTERVAL)


async def parse(
    url: str,
    timeout: float | None = None,
    max_scanned: int | None = None,
    max_found: int | None = None,
    found: set[URL] | None = None,
    scanned: set[URL] | None = None,
) -> tuple[set[URL], set[URL], StopReason]:
    url = URL(url)
    queue = UniqueQueue[URL]()
    queue.put_nowait(url)
    workers_number = 5

    if found is None:
        found = set()
        found.add(url)
    if scanned is None:
        scanned = set()

    reason = None

    try:
        async with asyncio.timeout(timeout):
            async with ClientSession() as session:
                try:
                    async with asyncio.TaskGroup() as tg:
                        for i in range(1, workers_number + 1):
                            name = f"worker-{i}"
                            tg.create_task(work(name, session, queue, found, scanned), name=name)

                        tg.create_task(
                            watch_for_numeric_limit(StopReason.FOUND_LIMIT, max_found, found),
                            name="found-watcher")
                        tg.create_task(
                            watch_for_numeric_limit(StopReason.SCANNED_LIMIT, max_scanned, scanned),
                            name="scanned-watcher")
                        tg.create_task(watch_for_scanning_completion(queue), name="completion-watcher")

                except* StopScanning as eg:
                    exception = cast(StopScanning, eg.exceptions[0])
                    if reason is None:
                        reason = exception.reason

    except asyncio.TimeoutError:
        module_logger.info("Got timeout limit")
        if reason is None:
            reason = StopReason.TIMEOUT

    return found, scanned, reason


async def main() -> None:
    url = "https://www.google.ru/"
    found, scanned, reason = await parse(url, max_scanned=2)
    module_logger.info("Total found %d", len(found))
    module_logger.info("Total scanned %d", len(scanned))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)5s.%(msecs)03d [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("parser.pages").setLevel(logging.INFO)

    asyncio.run(main())
