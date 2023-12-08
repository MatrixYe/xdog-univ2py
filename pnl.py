# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 定时任务，计算每日pnl
# -------------------------------------------------------------------------------
import logging
import sys
import time

import schedule

import config
import utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)
UNIV2_SWAP = 'univ2_swap'
UNIV2_TEMP = 'univ2_temp'
UNIV2_PNL = 'univ2_pnl'
UNIV2_PAIRS = 'univ2_pairs'


class Task:
    def __init__(self, c_path: str):
        self.conf = config.load_config(c_path)
        self.db = self._get_database()
        self.day = 3

        self.batch_size = 1000
        self.now_date = utils.now_date()

    def _get_database(self):
        mg = utils.connect_mongo(**self.conf.mongo.dict())
        return mg[self.conf.network]

    def _create_index(self):
        lg.info("create index...")
        self.db[UNIV2_TEMP].create_index([('trader', 1), ('pair', 1)])

        self.db[UNIV2_PNL].create_index([('date', 1)])
        self.db[UNIV2_PNL].create_index([('trader', 1)])
        self.db[UNIV2_PNL].create_index([('rea_pnl', -1)])

    @staticmethod
    def cal_st_et(day: int):
        et = int(time.time())
        st = et - 86400 * day
        return st, et

    def _handle_swap(self, swap):

        holder = self.db[UNIV2_TEMP].find_one({'trader': swap['trader'], 'pair': swap['pair']})
        if not holder:
            self._insert_pnl(swap)
        else:
            self._update_pnl(holder, swap)
            pass

    def _insert_pnl(self, swap):
        trader = swap.get('trader')
        pair = swap.get('pair')
        is_buy = swap.get('is_buy')
        amount = swap.get('amount')
        value = swap.get('value')
        coin_symbol = swap.get('coin_symbol')
        coin_addr = swap.get('coin_addr')
        # stable_symbol = swap.get('stable_symbol')
        if not is_buy or amount <= 0 or value <= 0:
            return
        data = {
            'trader': trader,
            'pair': pair,
            'coin_symbol': coin_symbol,
            'coin_addr': coin_addr,
            'hold': amount,
            'cost': value,
            'txs': 1,
            'rea_pnl': 0,

            'buy_tx': 1,
            'buy_amount': amount,  # 累计买入数量
            'buy_value': value,  # 累计买入价值
            'avg_buy_price': value / amount,

            'sell_tx': 0,  # 累计卖出次数
            'sell_amount': 0,  # 累计卖出数量
            'sell_value': 0,  # 累计卖出价值
            'avg_sell_price': 0
        }
        self.db[UNIV2_TEMP].insert_one(data)

    def _update_pnl(self, holder, swap):
        trader = swap.get('trader')
        pair = swap.get('pair')
        is_buy = swap.get('is_buy')
        amount = swap.get('amount')
        value = swap.get('value')
        if amount <= 0 or value <= 0:
            return

        if is_buy:
            # 后续买入
            u_txs = holder.get('txs') + 1
            u_buy_tx = holder.get('buy_tx') + 1
            u_buy_amount = holder.get('buy_amount') + amount
            u_buy_value = holder.get('buy_value') + value
            u_avg_buy_price = u_buy_value / u_buy_amount
            u_hold = holder.get('hold') + amount
            u_cost = holder.get('cost') + value
            update = {
                '$set': {
                    'txs': u_txs,
                    'buy_tx': u_buy_tx,
                    'buy_amount': u_buy_amount,
                    'buy_value': u_buy_value,
                    'avg_buy_price': u_avg_buy_price,
                    'hold': u_hold,
                    'cost': u_cost,
                }
            }
            self.db[UNIV2_TEMP].update_one({'trader': trader, 'pair': pair}, update)
        else:
            # 后续卖出
            u_txs = holder.get('txs') + 1
            u_sell_tx = holder.get('sell_tx') + 1
            u_sell_amount = holder.get('sell_amount') + amount
            u_sell_value = holder.get('sell_value') + value
            u_avg_sell_price = u_sell_value / u_sell_amount
            u_avg_buy_price = holder.get('avg_buy_price')
            u_hold = holder.get('hold') - amount
            u_cost = holder.get('cost') - value
            u_rea_pnl = u_sell_amount * (u_avg_sell_price - u_avg_buy_price)
            update = {
                '$set': {
                    'txs': u_txs,
                    'sell_tx': u_sell_tx,
                    'sell_amount': u_sell_amount,
                    'sell_value': u_sell_value,
                    'avg_sell_price': u_avg_sell_price,
                    'hold': u_hold,
                    'cost': u_cost,
                    'rea_pnl': u_rea_pnl,
                }
            }
            self.db[UNIV2_TEMP].update_one({'trader': trader, 'pair': pair}, update)

    def _delete_history(self):
        lg.info("delete history... ...")
        self.db.drop_collection(UNIV2_TEMP)

    def _state_swaps(self):
        st, et = self.cal_st_et(day=self.day)
        lg.info(f"start time:{st} end time:{et}")
        query = {
            'ts': {
                '$gte': st,
                '$lte': et
            }
        }
        total = self.db[UNIV2_SWAP].count_documents(filter=query)
        lg.info(f"total document:{total}")
        batch_size = self.batch_size
        skip = 0
        while skip < total:
            lg.info(
                f"total={total} skip={skip} batch={batch_size} progress={round(min(100 * (skip + batch_size) / total, 100), 2)}%")
            batch_documents = self.db[UNIV2_SWAP].find(filter=query).sort("_id").skip(skip).limit(batch_size)
            for document in batch_documents:
                self._handle_swap(document)

            skip += batch_size
        lg.info(f"complete hadle swap.")

    def _state_pnl(self):
        lg.info("start to state pnl... ...")
        total = self.db[UNIV2_TEMP].count_documents(filter={})
        pairs = self.db[UNIV2_TEMP].distinct(key='pair')
        # print(pairs)
        prices = self.db[UNIV2_PAIRS].find(filter={'_id': {'$in': pairs}}, projection={'_id': 1, 'price': 1})
        # prices = [a for a in prices]

        self.prices = {a['_id']: a['price'] for a in prices}
        # print(prices)
        lg.info(f"total temp document:{total}")
        batch_size = self.batch_size
        skip = 0
        while skip < total:
            lg.info(
                f"total={total} skip={skip} batch={batch_size} progress={round(min(100 * (skip + batch_size) / total, 100), 2)}%")
            batch_documents = self.db[UNIV2_TEMP].find(projection={'_id': 0}).sort([('_id', 1)]).skip(skip).limit(
                batch_size)
            for temp in batch_documents:
                self._handle_pnl(temp)

            skip += batch_size
        lg.info(f"complete hadle pnl.")

    def _handle_pnl(self, temp):
        trader = temp.get('trader')
        pair = temp.get('pair')
        hold = temp.get('hold')
        avg_buy_price = temp.get('avg_buy_price')
        txs = temp.get('txs')
        rea_pnl = temp.get('rea_pnl')
        current_price = self.prices[pair]
        flo_pnl = hold * (current_price - avg_buy_price)
        pnl = rea_pnl + flo_pnl
        if hold < 0 or current_price > 100:
            return
        query = {
            'date': self.now_date,
            'trader': trader
        }
        update = {
            '$inc': {
                'txs': txs,
                'rea_pnl': rea_pnl,
                'flo_pnl': flo_pnl,
                'pnl': pnl,
                'win': 1 if rea_pnl > 0 else 0,
                'kind': 1
            },
            '$push': {
                'items': temp
            }
        }
        self.db[UNIV2_PNL].find_one_and_update(filter=query, update=update, upsert=True)

    def _filter_pnl(self):
        lg.info("to filter pnl... ...")
        query = {'date': self.now_date}
        projection = {"_id": 1, "rea_pnl": 1}  # 保留 _id 和 pnl 字段，用于后续删除
        result = self.db[UNIV2_PNL].find(filter=query, projection=projection).sort([('rea_pnl', -1)]).limit(1000)
        ids_to_keep = [document["_id"] for document in result]
        delete_query = {'date': self.now_date, "_id": {"$nin": ids_to_keep}}
        self.db[UNIV2_PNL].delete_many(delete_query)
        lg.info("filter pnl complent... ...")

    def job(self):
        self._delete_history()
        self._create_index()
        self._state_swaps()
        self._state_pnl()
        self._filter_pnl()

    def testjob(self):
        print("this is test jon!!!")
        self._state_pnl()
        self._filter_pnl()

    def run(self):
        lg.info("start job,good luck!")
        schedule.every().day.at("00:02").do(self.job)  # 每日更新一次
        while True:
            schedule.run_pending()
            time.sleep(0.1)


def c_arg() -> str:
    try:
        return sys.argv[1]
    except Exception as e:
        raise e


if __name__ == '__main__':
    c = c_arg()
    lg.info(f"input config file path:{c}")
    task = Task(c)
    task.run()
