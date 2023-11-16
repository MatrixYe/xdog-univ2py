# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 同步池子数据从pg到mongo
# -------------------------------------------------------------------------------
# 定义每页的行数和起始页码
import time

import psycopg2
from pymongo import MongoClient

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
ETHSCANURL = "https://api.etherscan.io/api?module=stats&action=ethprice&apikey=611NRNEEQ9ZAV5E4K7P88MWG3QD6AKNKNT"
# 定义数据库连接参数
db_params = {
    'host': 'localhost',  # 数据库主机名
    'port': 5001,
    'database': 'postgres',  # 数据库名
    'user': 'root',  # 数据库用户名
    'password': 'password'  # 数据库密码
}
mg_parms = {
    "host": "localhost",
    "port": 5004,
    "username": "root",
    "password": "password"
}
page_size = 1000  # 你可以根据需要修改每页的行数
tabe_name = "pairs"

db_name = 'ethereum'
coll_name = 'univ2_pairs'
debug = False
mg = MongoClient(**mg_parms)


# def weth_price():
#     resp = requests.get(ETHSCANURL)
#     if resp.status_code == 200 and resp.json()['status'] == "1":
#         price = resp.json()['result']['ethusd']
#         print(f"获取eth价格{price}")
#         return float(price)
#     else:
#         raise "error etherscan!"
#         # print("error etherscan! ")
#         # return None


def cal_stable_index(t0: str, t1: str) -> int:
    if t0.lower() == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":
        return 0
    if t1.lower() == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":
        return 1
    return -1


def handle_row(row):
    # 行数据解包
    id_, pair, token0, token1, p_index, reserve0, reserve1, token0_symbol, token0_decimal, token1_symbol, token1_decimal, create_block, create_time, create_tx_hash, creator, update_block, update_time, update_tx_hash, pair_type, price0, price1 = row
    stable_index = cal_stable_index(token0, token1)
    if stable_index == -1 or not token0_symbol or not token1_symbol:
        print(f"not weth pair: {pair}")
        return
    new_pair_data = {
        '_id': pair.lower(),
        'pair': pair.lower(),
        'pindex': p_index,
        'name': f"{token0_symbol}/{token1_symbol}" if stable_index == 1 else f"{token1_symbol}/{token0_symbol}",
        'coin_addr': token0.lower() if stable_index == 1 else token1.lower(),
        'coin_symbol': token0_symbol if stable_index == 1 else token1_symbol,
        'coin_decimal': token0_decimal if stable_index == 1 else token1_decimal,

        'stable_addr': token1.lower() if stable_index == 1 else token0.lower(),
        'stable_symbol': token1_symbol if stable_index == 1 else token0_symbol,
        'stable_decimal': token1_decimal if stable_index == 1 else token0_decimal,

        'stable_index': stable_index,
        # 'create_time': create_time,
        # 'create_block': create_block,
        # 'create_tx': create_tx_hash.lower(),
        # 'creator': creator.lower(),
        'price': float(price0) if stable_index == 1 else float(price1),
        'coin_reserve': int(reserve0) / 10 ** token0_decimal if stable_index == 1 else int(
            reserve1) / 10 ** token1_decimal,

        'stable_reserve': int(reserve1) / 10 ** token1_decimal if stable_index == 1 else int(
            reserve0) / 10 ** token0_decimal,
    }
    #             'create_time': ts,
    #             'create_block': event['block_number'],
    #             'create_tx': tx['tx_hash'],
    #             'creator': tx['from']
    # update_block, update_time, update_tx_hash
    if create_time:
        new_pair_data['create_time'] = create_time
    if creator:
        new_pair_data['creator'] = creator
    if create_block:
        new_pair_data['create_block'] = create_block
    if create_tx_hash:
        new_pair_data['create_tx'] = create_tx_hash
    if update_time:
        new_pair_data['update_time'] = update_time

    try:
        result = mg[db_name][coll_name].insert_one(new_pair_data)
        if result.inserted_id:
            print(f"success insert pair {pair}")
    except Exception as e:
        print(f"ERROR:{e}")
        print(f"failed insert pair {pair}")
        raise e


def run():
    st = time.time()
    if debug:
        mg[db_name].drop_collection(coll_name)
    try:
        # 给字段加索引
        # 连接到 PostgreSQL 数据库
        connection = psycopg2.connect(**db_params)
        # 创建一个游标对象，用于执行 SQL 查询
        cursor = connection.cursor()
        # 查询总行数
        cursor.execute(f"SELECT COUNT(*) FROM {tabe_name}")
        total_rows = cursor.fetchone()[0]
        print(f"find total rows count:{total_rows}")
        start_page = 1
        # 分页查询并遍历数据
        while start_page <= (total_rows // page_size) + 1:
            offset = (start_page - 1) * page_size
            print(f"query row by page:{start_page} page size:{page_size} offset:{offset}")
            query = f"SELECT * FROM {tabe_name} ORDER BY id LIMIT {page_size} OFFSET {offset}"  # 替换 your_table 和排序列名
            cursor.execute(query)
            rows = cursor.fetchall()
            # 处理行数据
            for row in rows:
                handle_row(row)
            if debug:
                return
            start_page += 1

        # 关闭游标和数据库连接
        cursor.close()
        connection.close()
    except Exception as error:
        print("Error :", error)
        return
    finally:
        et = time.time()
        print(f"End query,time cast:{et - st}s")


if __name__ == '__main__':
    run()
