# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import logging
import threading
import time

import schedule

from task1 import run as t1
from task2 import run as t2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)


# 并发执行
def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


if __name__ == '__main__':
    schedule.every(5).seconds.do(run_threaded, t1)
    schedule.every(4).seconds.do(run_threaded, t2)
    while True:
        schedule.run_pending()
        time.sleep(1)
