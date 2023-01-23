import asyncio
import logging
from typing import Coroutine, Any, TypeVar, Generic

from aiohttp import ClientSession
from yarl import URL

from parser.pages import Host, normalize_url, scan_page

T = TypeVar("T")
module_logger = logging.getLogger("parser.web")


class UniqueQueue(Generic[T]):
    """Wrapper for asyncio.Queue receiving only unique elements."""

    def __init__(self):
        self._queue = asyncio.Queue()
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


async def work(name: str, session: ClientSession, queue: UniqueQueue[URL], found: set[URL], scanned: set[URL]):
    logger = module_logger.getChild(name)

    while True:
        url = await queue.get()
        host = Host(url.host)
        logger.info("Started scanning: %s", url)

        try:
            async with session.get(url, allow_redirects=False) as response:
                if response.status in (301, 302):
                    raw_redirect = response.headers["location"]
                    logger.info("Got redirect %d: %s", response.status, raw_redirect)

                    if redirect_url := normalize_url(url, host, raw_redirect):
                        queue.put_nowait(redirect_url)
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

                logger.info("Found links: %d new, %d total", len(found) - found_before, len(page_links))
                logger.debug("Current queue size is %d", queue.qsize())

        finally:
            queue.task_done()


async def watch_for_workers(queue: UniqueQueue, workers: list[asyncio.Task]):
    await queue.join()
    module_logger.info("Scanning finished")

    for worker in workers:
        worker.cancel()


async def parse(url: str) -> tuple[set[URL], set[URL]]:
    url = URL(url)
    queue = UniqueQueue()
    queue.put_nowait(url)

    found = {url}
    scanned = set()
    workers_number = 10

    async with ClientSession() as session:
        async with asyncio.TaskGroup() as tg:
            workers = []

            for i in range(1, workers_number + 1):
                name = f"worker-{i}"
                worker = tg.create_task(work(name, session, queue, found, scanned), name=name)
                workers.append(worker)

            tg.create_task(watch_for_workers(queue, workers), name="watcher")

    print(len(found))
    print(len(scanned))
    return found, scanned


async def main():
    url = "https://www.google.ru/"
    # url = "https://dvmn.org/modules/"
    await parse(url)


if __name__ == "__main__":
    logging.basicConfig(
        format=u"%(asctime)5s.%(msecs)03d [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
    logging.getLogger("parser.pages").setLevel(logging.INFO)

    asyncio.run(main())
