# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import asyncio


async def task():
    print("start parse event ... ...")
    while True:
        print("parse...")
        await asyncio.sleep(10)
