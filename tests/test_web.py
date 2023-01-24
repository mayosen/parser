import asyncio

import pytest

from parser.web import UniqueQueue


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
        assert isinstance(eg.value.exceptions[0], ValueError)

    async def test_putting_duplicates(self):
        queue = UniqueQueue()
        queue.put_nowait(1)
        queue.put_nowait(2)
        assert queue.qsize() == 2

        queue.put_nowait(1)
        queue.put_nowait(2)
        assert queue.qsize() == 2
