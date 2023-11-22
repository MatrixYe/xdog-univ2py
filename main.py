# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import asyncio
import logging

import requests

from sync import task as sync_task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)


async def main():
    # tasks = [sync_task(), parse_task()]
    tasks = [sync_task()]
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        err_msg = f"Project:xdog-univ2py\nError:{e}"
        lg.error(err_msg)
        push_error(err_msg)


def push_error(msg: str):
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/e9078a15-fac0-4957-a76d-cdd2c309a812"
    text = {
        "msg_type": "text",
        "content":
            {
                "text": msg
            }
    }
    requests.post(url=url,
                  json=text)


if __name__ == '__main__':
    asyncio.run(main())
