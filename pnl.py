# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------

# 定时任务，计算pnl
from pymongo import MongoClient

from config import load_config

conf = load_config('./config.toml')
mg = MongoClient(host=conf.mongo.host, port=conf.mongo.port, password=conf.mongo.password)


def cal_pnl():
    pass
