# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 将erc20 代币进行数据转移，从pg到mg
# -------------------------------------------------------------------------------
#
import time

import psycopg2
import requests
from pymongo import MongoClient

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
ETHSCANURL = "https://api.etherscan.io/api?module=stats&action=ethprice&apikey=611NRNEEQ9ZAV5E4K7P88MWG3QD6AKNKNT"
# 定义数据库连接参数
host = "localhost"
db_params = {
    'host': host,  # 数据库主机名
    'port': 5001,
    'database': 'postgres',  # 数据库名
    'user': 'root',  # 数据库用户名
    'password': 'password'  # 数据库密码
}
mg_parms = {
    "host": host,
    "port": 5004,
    "username": "root",
    "password": "password"
}
page_size = 1000  # 你可以根据需要修改每页的行数
tabe_name = "erc20"
debug = False
db_name = 'ethereum'
coll_name = 'tokens'

mg = MongoClient(**mg_parms)


def weth_price():
    resp = requests.get(ETHSCANURL)
    if resp.status_code == 200 and resp.json()['status'] == "1":
        price = resp.json()['result']['ethusd']
        print(f"获取eth价格{price}")
        return float(price)
    else:
        print("error etherscan! ")
        return None


# ep = weth_price()
# print(f"weth price:{ep} USD")


def handle_row(row):
    id_, address, symbol, decimal = row
    # print(id_, address, symbol, decimal)
    try:
        if not address or not symbol or not decimal:
            print(f"pass token:{address} {symbol} {decimal}")
            return
        result = mg[db_name][coll_name].insert_one(document={
            '_id': address.lower(),
            'address': address.lower(),
            'type': 'erc20',
            'symbol': symbol,
            'decimal': decimal
        })
        if result.inserted_id:
            print(f"insert token:{address} SUCCESS")
        else:
            print(f"pass:{address}")
    except Exception as e:
        print(f"Exception:{e}")


def run():
    st = time.time()
    try:
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
