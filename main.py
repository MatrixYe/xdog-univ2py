# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import asyncio
import logging

from sync import task as sync_task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)


async def main():
    # tasks = [sync_task(), parse_task()]
    tasks = [sync_task()]
    for coro in asyncio.as_completed(tasks):
        try:
            await coro
        except Exception as e:
            lg.error(e)


if __name__ == '__main__':
    print("hello")
    asyncio.run(main())
