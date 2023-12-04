# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import time

import config
import utils

# 定时任务，计算pnl

UNIV2_SWAP = 'univ2_swap'


class Task:
    def __init__(self):
        self.conf = config.load_config('./config.toml')
        self.db = self._get_database()
        self.day = 30
        self.batch_size = 1000

    def _get_database(self):
        mg = utils.connect_mongo(**self.conf.mongo.dict())
        return mg[self.conf.network]

    @staticmethod
    def cal_st_et(day: int):
        et = int(time.time())
        st = et - 86400 * day
        return st, et

    def _handle_swap(self, swap):
        # print(swap)
        pass

    def run(self):
        print(self.db['univ2_base'].find_one({'_id': 1}))
        st, et = self.cal_st_et(day=self.day)
        print(st, et)
        query = {
            'ts': {
                '$gte': st,
                '$lte': et
            }
        }
        total_documents = self.db[UNIV2_SWAP].count_documents(filter=query)
        print(total_documents)
        batch_size = self.batch_size
        skip = 0
        while skip < total_documents:
            batch_documents = self.db[UNIV2_SWAP].find(filter=query).sort("_id").skip(skip).limit(batch_size)

            for document in batch_documents:
                self._handle_swap(document)

            skip += batch_size
            print('skip... ...')


if __name__ == '__main__':
    task = Task()
    task.run()
