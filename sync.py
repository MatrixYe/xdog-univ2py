# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import asyncio
import logging

from pymongo import MongoClient
from web3 import Web3, HTTPProvider
from web3.contract import Contract

from config import load_config, Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)

BASE = "univ2_base"


class Task:

    def __init__(self):
        self.conf: Config = self._load_config()
        self._factory_abi = self._read_factory_abi()
        self._pair_abi = self._read_pair_abi()
        self._erc20_abi = self._read_erc20_abi()

        self.db = self._fetch_database()
        self.w3 = self._load_eth_client()
        self.factory_instance = self._gen_factory_instance(self.conf.factory)

    # 获取数据库，根据网络名称命名，如ethereum，这样可支持多链数据同步
    def _fetch_database(self):
        mg = self._load_mongo()
        return mg[self.conf.network]

    @staticmethod
    def _load_config() -> Config:
        return load_config("./config.toml")

    # 加载mongo客户端
    def _load_mongo(self):
        host = self.conf.mongo.host
        port = self.conf.mongo.port
        username = self.conf.mongo.username
        password = self.conf.mongo.password
        client = MongoClient(host=host, port=port, username=username, password=password)
        return client

    # 加载以太坊客户端
    def _load_eth_client(self) -> Web3:
        return Web3(HTTPProvider(endpoint_uri=self.conf.node_url))

    # 获取本地同步最新的uniswap v2 pair index
    def _get_local_pair_index(self):
        result = self.db[BASE].find_one(filter={'_id': 1})
        return result['pair_index']

    # 设置最新同步uniswap v2池子索引
    def _set_local_pair_index(self, index: int):
        self.db[BASE].update_one(filter={'_id': 1}, update={'$set': {'pair_index': index}})

    # 初始化操作
    def _initsysctrl(self):
        result = self.db[BASE].find_one({"_id": 1})
        if not result:
            print("base is  not exist")
            data = {
                '_id': 1,
                'pair_index': -1,  # 没有同步时，新开始的索引为0=-1 +1
                'start_block': self.conf.start_block,
                'sync_block': self.conf.start_block,
                'parse_block': self.conf.start_block
            }
            self.db[BASE].insert_one(data)
        else:
            print("base is exist")
            print(result)

        # todo  初始化其他集合，索引等操作

    def _fetch_logs(self, start_block, end_block):
        try:
            logs = self.w3.eth.get_logs(filter_params={
                'fromBlock': start_block,
                'toBlock': end_block,
                # 'address': self.w3.to_checksum_address(self.config['tomo_address'])
            })
            return logs
        except Exception as e:
            lg.error(e)

    # 构建factory实例
    def _gen_factory_instance(self, factory_address: str) -> Contract:
        contract_address = self.w3.to_checksum_address(factory_address)
        return self.w3.eth.contract(address=contract_address, abi=self._factory_abi)

    # 构建pair实例
    def _gen_pair_instance(self, pair_address: str) -> Contract:
        contract_address = self.w3.to_checksum_address(pair_address)
        return self.w3.eth.contract(address=contract_address, abi=self._pair_abi)

    # 构建erc20 tolen 实例
    def _gen_erc20_instance(self, erc20_address: str) -> Contract:
        contract_address = self.w3.to_checksum_address(erc20_address)
        return self.w3.eth.contract(address=contract_address, abi=self._erc20_abi)

    def _get_remote_pair_index(self) -> int:
        func = getattr(self.factory_instance.functions, 'allPairsLength')()
        result = func.call()
        lg.info(f"get remote pair index is {result}")
        return result

    # 核心功能代码入口
    async def run(self):
        self._initsysctrl()
        while True:
            num = self.w3.eth.block_number
            print(f"block number  is {num}")
            await asyncio.sleep(5)

    async def debug(self):
        # self._initsysctrl()
        self._to_sync_signpair(280000)
        # while True:
        #     x = self._get_local_pair_index()
        #     y = self._get_remote_pair_index()  # 测试获取远程的pair 最新索引
        #     x = -1
        #     y = 15
        #     print("x=", x)
        #     print("y=", y)
        #     break
        # if x == y:
        #     break
        # for i in range(x + 1, y + 1):
        #     print(f"to sync pair in {i}")
        #     self._to_sync_signpair(i)
        #     self._set_local_pair_index(i)

        # print(x)

    def _to_sync_signpair(self, i):
        lg.info(f"to sync pair index:{i}")
        result = getattr(self.factory_instance.functions, 'allPairs')(i).call()
        lg.info(f"pair address is : {result}")
        pair_instance = self._gen_pair_instance(result)
        token0 = getattr(pair_instance.functions, "token0")().call()
        token1 = getattr(pair_instance.functions, "token1")().call()
        print(f"token0={token0} token1={token1}")
        # self._gen_erc20_instance()
        self._fetch_erc20(addr=token0)

        pass

    def _fetch_erc20(self, addr: str):
        # todo 优先从本地

        pass

    def _get_local_erc20(self):
        pass

    @staticmethod
    def _read_factory_abi():
        with open('./source/abi/UniswapV2Factory.abi', 'r') as f:
            return f.read()

    @staticmethod
    def _read_pair_abi():
        with open('./source/abi/IUniswapV2Pair.abi', 'r') as f:
            return f.read()

    @staticmethod
    def _read_erc20_abi():
        with open('./source/abi/IERC20.abi', 'r') as f:
            return f.read()


async def task():
    print("start to sync ... ...")
    await Task().debug()
