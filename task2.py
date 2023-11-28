# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import time

import utils

rds = utils.connect_redis(host='127.0.0.1', port=5005, password="password")


def run():
    print("this is task 2")
    print(rds.get("hello"))
    v = rds.get("hello")
    if v:
        print(v)
    else:
        rds.set(name="hello", value=int(time.time()), ex=10)
