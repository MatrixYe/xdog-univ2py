# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import asyncio


async def task1(queue, n: int):
    for i in range(1, int(n / 2)):
        p = 2 * i - 1
        print(f"Task-1 print {p}")
        await queue.put(p)
        await asyncio.sleep(0.1)
    await queue.put(None)


async def task2(queue):
    while True:
        p = await queue.get()
        if p is None:
            break
        print(f"Task-2 print {p + 1}")
        await asyncio.sleep(1)


async def main():
    queue = asyncio.Queue()
    tasks = [task1(queue, 10), task2(queue)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # asyncio.run(main())
    x = 2000000 / 10 ** 2
    print(x)
