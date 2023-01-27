import asyncio

import aiohttp
import httpbin
import pytest
from pytest_httpbin import serve

from parser.web import StopReason, UniqueQueue, parse


class TestUniqueQueue:
    async def test_size(self):
        queue = UniqueQueue()
        assert queue.qsize() == 0

        queue.put_nowait(0)
        assert queue.qsize() == 1

        await queue.get()
        assert queue.qsize() == 0

    async def test_flow(self):
        queue = UniqueQueue()
        numbers = (1, 2, 3)

        for i in numbers:
            queue.put_nowait(i)

        for i in numbers:
            assert await queue.get() == i

    async def test_join(self):
        queue = UniqueQueue()
        numbers = (1, 2, 3)

        for i in numbers:
            queue.put_nowait(i)

        async def stop(q: UniqueQueue):
            await q.join()
            raise ValueError

        async def consume(q: UniqueQueue):
            while True:
                await q.get()
                q.task_done()

        with pytest.raises(ExceptionGroup) as eg:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(consume(queue))
                tg.create_task(stop(queue))

        assert len(eg.value.exceptions) == 1
        exception = eg.value.exceptions[0]
        assert isinstance(exception, ValueError)

    async def test_putting_duplicates(self):
        queue = UniqueQueue()
        queue.put_nowait(1)
        queue.put_nowait(2)
        assert queue.qsize() == 2

        queue.put_nowait(1)
        queue.put_nowait(2)
        assert queue.qsize() == 2


@pytest.fixture(scope="session")
def server():
    server = serve.Server(host="127.0.0.1", port=5000, application=httpbin.app)
    server.start()
    yield server
    server.stop()


async def parse_str(url: str, **kwargs) -> tuple[set[str], set[str], StopReason]:
    found, scanned, reason = await parse(url, **kwargs)
    return {str(url) for url in found}, {str(url) for url in scanned}, reason


class TestParse:
    async def test_auto_scanning_completion(self, server):
        found, scanned, reason = await parse_str(f"{server.url}/links/5/0")
        expected = {f"{server.url}/links/5/{i}" for i in range(5)}
        assert found == expected
        assert scanned == expected
        assert reason == StopReason.ALL_PROCESSED

    async def test_scanning_timeout(self, server):
        url = f"{server.url}/delay/2"
        found, scanned, reason = await parse_str(url, timeout=0.1)
        assert found == {url}
        assert scanned == set()
        assert reason == StopReason.TIMEOUT

    async def test_request_timeout(self, server):
        url = f"{server.url}/delay/2"
        found, scanned, reason = await parse_str(url, request_timeout=aiohttp.ClientTimeout(total=0.1))
        assert found == {url}
        assert scanned == set()
        assert reason == StopReason.ALL_PROCESSED

    async def test_redirect(self, server):
        url = f"{server.url}/redirect/1"
        found, scanned, reason = await parse_str(url)
        expected = {
            url,
            f"{server.url}/get"
        }
        assert found == expected
        assert scanned == expected
        assert reason == StopReason.ALL_PROCESSED

    async def test_redirect_n_times(self, server):
        url = f"{server.url}/redirect/5"
        found, scanned, reason = await parse_str(url)
        expected = {
            url,
            f"{server.url}/get",
            *{f"{server.url}/relative-redirect/{i}" for i in range(4, 0, -1)}
        }
        assert found == expected
        assert scanned == expected
        assert reason == StopReason.ALL_PROCESSED

    async def test_redirect_to_other(self, server):
        url = f"{server.url}/redirect-to?url=http://example.org&status_code=302"
        found, scanned, reason = await parse_str(url)
        assert found == {url}
        assert scanned == {url}
        assert reason == StopReason.ALL_PROCESSED

    async def test_max_scanned(self, server):
        limit = 10
        found, scanned, reason = await parse_str(f"{server.url}/links/50/0", max_scanned=limit, check_interval=0)
        assert abs(len(scanned) - limit) <= 1
        assert reason == StopReason.SCANNED_LIMIT

    async def test_max_found(self, server):
        found, scanned, reason = await parse_str(f"{server.url}/links/10/0", max_found=10, check_interval=0)
        assert len(scanned) == 1
        assert len(found) == 10
        assert reason == StopReason.FOUND_LIMIT
