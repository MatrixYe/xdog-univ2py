# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
from pymongo import MongoClient
from redis import StrictRedis


# 连接mongodb数据库
def connect_mongo(host: str, port: int, username: str, password: str, db: str):
    client = MongoClient(host=host, port=port, username=username, password=password)
    return client[db]


def connect_redis(host: str, port: int, password: str, db=0):
    redis_client = StrictRedis(host=host, port=port, password=password, db=db, decode_responses=True)
    return redis_client
