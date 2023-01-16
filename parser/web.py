import asyncio
import logging
from typing import Coroutine, Any

from aiohttp import ClientSession

from parser.pages import scan_page

module_logger = logging.getLogger("parser.web")


class UniqueQueue:
    """Wrapper on asyncio.Queue containing only unique elements."""

    def __init__(self):
        self._queue = asyncio.Queue()
        self._values = set()

    async def get(self) -> Any:
        item = await self._queue.get()
        self._values.remove(item)
        return item

    def put_nowait(self, item) -> None:
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


async def work(name: str, session: ClientSession, queue: UniqueQueue, found: set[str], scanned: set[str]):
    logger = module_logger.getChild(name)

    while True:
        url = await queue.get()

        try:
            if url in scanned:
                logger.info("Already scanned: %s", url)
                continue

            logger.info("Started scanning: %s", url)

            # TODO: Process redirects
            async with session.get(url, allow_redirects=False) as response:
                html = await response.text()
                page_links = await scan_page(url, html)
                scanned.add(url)

                new_links = page_links - scanned
                logger.info("Found links: %d new, %d total", len(new_links), len(page_links))
                found.update(new_links)

                for link in new_links:
                    queue.put_nowait(link)

                logger.debug("Current queue size is %d", queue.qsize())

        finally:
            queue.task_done()


async def watch_workers(queue: UniqueQueue, workers: list[asyncio.Task]):
    await queue.join()
    module_logger.info("Scanning finished")

    for worker in workers:
        worker.cancel()


async def parse(url: str) -> tuple[set[str], set[str]]:
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
                task = tg.create_task(work(name, session, queue, found, scanned), name=name)
                workers.append(task)

            tg.create_task(watch_workers(queue, workers), name="watcher")

    print(len(found))
    print(len(scanned))
    return scanned, found


async def main():
    url = "https://www.google.ru/"
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
