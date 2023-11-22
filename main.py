# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import logging
import time

import schedule

from deco import catch_exceptions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)


@catch_exceptions(cancel_on_failure=False)
def task():
    a = 1 / 0


if __name__ == '__main__':
    schedule.every(5).seconds.do(task)
    while True:
        schedule.run_pending()
        time.sleep(1)
