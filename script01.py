# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import time

from pymongo import MongoClient

client = MongoClient(host="localhost", port=5004, username="root", password="password")
base = client["ethereum"]["univ2_base"].find_one({'_id': 1})
print(base)
t = int(time.time()) - 86400 * 60
print(f"to delete data:ts<{t}")
result = client["ethereum"]["univ2_event"].delete_many(filter={
    "ts": {
        "$lte": t
    }
})
print(result.deleted_count)

result = client["ethereum"]["univ2_kline"].delete_many(filter={
    "start_time": {
        "$lte": t
    }
})
print(result.deleted_count)

result = client["ethereum"]["univ2_swap"].delete_many(filter={
    "ts": {
        "$lte": t
    }
})
print(result.deleted_count)
