# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------

# 定时任务，计算pnl

from config import load_config

# conf = load_config('./config.toml')
# mg = MongoClient(host=conf.mongo.host, port=conf.mongo.port, password=conf.mongo.password)
# mg = utils.connect_mongo(host=conf.mongo.host, port=conf.mongo.port, username=conf.mongo.username,
#                          password=conf.mongo.password)

f = load_config('./config.toml')

if __name__ == '__main__':
    print("this is pnl。。。 。。。")
    print(f)
