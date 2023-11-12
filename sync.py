# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import asyncio
import json
import logging
from typing import Any

import aioredis
from eth_abi import abi
from pymongo import MongoClient
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.contract import AsyncContract

from config import load_config, Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lg = logging.getLogger(__name__)

BASE = "univ2_base"
TOKENS = "tokens"
UNIV2_PAIRS = "univ2_pairs"
UNIV2_EVENT = "univ2_event"


class Task:

    def __init__(self):
        self.conf: Config = self._load_config()
        self._factory_abi = self._read_factory_abi()
        self._pair_abi = self._read_pair_abi()
        self._erc20_abi = self._read_erc20_abi()

        self.db = self._connect_mongo()
        self.rs = self._connect_redis()
        self.w3 = self._load_eth_client()
        self.factory_instance = self._gen_factory_instance(self.conf.factory)

    # 初始化操作
    def _initsysctrl(self):
        result = self._get_base()
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
            lg.info(f"base:{result}")

        # todo  初始化其他集合，索引等操作

    def _connect_redis(self):
        host = self.conf.redis.host
        port = self.conf.redis.port
        password = self.conf.redis.password
        db = self.conf.redis.db
        redis_client = aioredis.StrictRedis(host=host, port=port, password=password, db=db, decode_responses=True)
        return redis_client

    # 获取数据库，根据网络名称命名，如ethereum，这样可支持多链数据同步
    def _connect_mongo(self):
        host = self.conf.mongo.host
        port = self.conf.mongo.port
        username = self.conf.mongo.username
        password = self.conf.mongo.password
        client = MongoClient(host=host, port=port, username=username, password=password)
        return client[self.conf.network]

    # 加载以太坊客户端
    def _load_eth_client(self) -> AsyncWeb3:
        return AsyncWeb3(AsyncHTTPProvider(endpoint_uri=self.conf.node_url))

    # 获取本地同步最新的uniswap v2 pair index
    def _get_local_pair_index(self) -> int:
        result = self._get_base()
        return result['pair_index']

    # 设置最新同步uniswap v2池子索引
    def _set_local_pair_index(self, index: int):
        self._update_base("pair_index", index)

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
    def _gen_factory_instance(self, factory_address: str) -> AsyncContract:
        contract_address = self.w3.to_checksum_address(factory_address)
        return self.w3.eth.contract(address=contract_address, abi=self._factory_abi)

    # 构建pair实例
    def _gen_pair_instance(self, pair_address: str) -> AsyncContract:
        contract_address = self.w3.to_checksum_address(pair_address)
        return self.w3.eth.contract(address=contract_address, abi=self._pair_abi)

    # 构建erc20 tolen 实例
    def _gen_erc20_instance(self, erc20_address: str) -> AsyncContract:
        contract_address = self.w3.to_checksum_address(erc20_address)
        return self.w3.eth.contract(address=contract_address, abi=self._erc20_abi)

    async def _get_remote_pair_index(self) -> int:
        try:
            index = await getattr(self.factory_instance.functions, 'allPairsLength')().call()
            return index
        except Exception as e:
            lg.error(e)
            return 0

    # 核心功能代码入口
    async def run(self):
        self._initsysctrl()
        # 全量同步池子信息
        # await self._sync_all_pairs()
        await self._loop()

    async def _loop(self):
        # print("this is loop")
        # await asyncio.sleep(3)

        while True:
            x = self._get_sync_block()
            y = await self._get_remote_block_number()
            lg.info(f"loop sync local block:{x} remote block:{y}")
            if y == 0:
                lg.error("failed to get remote block!")
                await asyncio.sleep(self.conf.sync_interval)
                continue
            if x > y:
                lg.warning("local block > remote block")
                await asyncio.sleep(self.conf.sync_interval)
                continue

            if x == y:
                print("local block = remote block")
                await asyncio.sleep(self.conf.sync_interval)
                continue
            for i in range(x + 1, y + 1):
                print(f"to scan block {i}")
                await self._to_scan_block(i)
                self._set_sync_block(i)
                return

    def _get_pair(self, addr: str):
        self.db[UNIV2_PAIRS].find_one({'_id': addr.lower()})

    async def _fetch_tx(self, tx_hash) -> (str, str):
        cache = await self.rs.get(tx_hash)
        if cache:
            print(f"cache is exist:{tx_hash}")
            data = json.loads(cache)
            return data['from'].lower(), data['to'].lower()
        else:
            print(f"cache is not exist:{tx_hash}")
            tx = await self.w3.eth.get_transaction(tx_hash)
            data = json.dumps({'from': tx['from'].lower(), 'to': tx['to'].lower()})
            print(data)
            await self.rs.set(tx_hash, data, 120)
            return tx['from'], tx['to']

    async def _to_scan_block(self, i: int):
        block = await self.w3.eth.get_block(i)
        ts = block['timestamp']
        logs = await self.w3.eth.get_logs(filter_params={
            'fromBlock': i,
            'toBlock': i,
            # 'address': self.w3.to_checksum_address(self.config['tomo_address'])
        })
        for log in logs:
            tx_hash = log.get("transactionHash").hex()
            contract_addr = log.get('address').lower()
            if contract_addr == self.conf.factory.lower():
                # 这是factory合约抛出来的event
                (from_, to) = await self._fetch_tx(tx_hash)
                print(f"这是factory合约抛出来的event,ts={ts} from={from_} to={to}")
                self._handle_factory_event(ts, from_, to, log)
                continue
            if self._get_pair(contract_addr):
                # 这是pair合约抛出来的event
                (from_, to) = await self._fetch_tx(tx_hash)
                print(f"这是pair合约抛出来的event,ts={ts} from={from_} to={to}")
                self._handle_pair_event(ts, from_, log)
                continue

    # 获取远程block高度
    async def _get_remote_block_number(self) -> int:
        try:
            num = await self.w3.eth.block_number
            return num
        except Exception as e:
            lg.error(e)
            return 0

    # 获取本地同步sync高度
    def _get_sync_block(self) -> int:
        base = self._get_base()
        return base.get('sync_block')

    def _set_sync_block(self, height: int):
        self._update_base('sync_block', height)

    def _get_base(self):
        return self.db[BASE].find_one({'_id': 1})

    def _update_base(self, field: str, new_data: Any):
        self.db[BASE].update_one({'_id': 1}, {'$set': {field: new_data}})

    async def _sync_all_pairs(self):
        lg.info(f"sync_all_pairs:{self.conf.full_pair}")
        while self.conf.full_pair:
            x = self._get_local_pair_index()
            y = await self._get_remote_pair_index()  # 获取远程的pair 最新索引
            lg.info(f"get local pair index:{x},get remote pair index{y}")
            if not y:
                lg.warning("failed to get remote block!")
                break
            if x > y:
                lg.warning(f"local pair index:{x} > remote pair index!what happen")
                break
            if x == y:
                break
            for i in range(x + 1, y + 1):
                await self._to_sync_signpair(i)
                self._set_local_pair_index(i)
                if i == x + 3:
                    lg.info(f"sync_all_pairs is complete!")
                    return
        lg.info(f"sync_all_pairs is complete!")

    async def debug(self):
        await self._to_scan_block(18557877)
        # tx = await self._fetch_tx("0x406df6e4f04d337e323b7710c6a6dfea34b6967177b31175c2909efdfd83b32f")
        # print(tx)

    async def _to_sync_signpair(self, i: int):
        lg.info(f"to sync pair index:{i}")
        pair_addr: str = await getattr(self.factory_instance.functions, 'allPairs')(i).call()

        lg.info(f"pair address is : {pair_addr}")
        pair_instance = self._gen_pair_instance(pair_addr)
        token0 = await getattr(pair_instance.functions, "token0")().call()
        token1 = await getattr(pair_instance.functions, "token1")().call()
        lg.info(f"token0={token0} token1={token1}")
        t0_info = await self._fetch_erc20(addr=token0)
        t1_info = await self._fetch_erc20(addr=token1)
        if not t0_info or not t1_info:
            lg.warning(f"token0:{token0} or token1{token1} is not a norm erc20 token --> pass")
            return
        t0_addr = t0_info['address']
        t0_symbol = t0_info['symbol']
        t0_decimal = t0_info['decimal']
        t1_addr = t1_info['address']
        t1_symbol = t1_info['symbol']
        t1_decimal = t1_info['decimal']
        self._to_save_pair(i, pair_addr, t0_addr, t0_symbol, t0_decimal, t1_addr, t1_symbol, t1_decimal)

    def _to_save_pair(self,
                      pindex: int,
                      pair_addr: str,
                      t0_addr: str,
                      t0_symbol: str,
                      t0_decimal: int,
                      t1_addr: str,
                      t1_symbol: str,
                      t1_decimal: int):
        lg.info(f"to save pair:{pair_addr.lower()}")
        if t1_symbol in ["WETH", "USDC", "USCT", "DAI"]:
            # coin is t0
            data = {
                '_id': pair_addr.lower(),
                'pindex': pindex,
                'pair': pair_addr.lower(),
                'name': f"{t0_symbol}/{t1_symbol}",
                'coin_addr': t0_addr.lower(),
                'coin_symbol': t0_symbol,
                'coin_decimal': t0_decimal,
                'stable_addr': t1_addr.lower(),
                'stable_symbol': t1_symbol,
                'stable_decimal': t1_decimal
            }
            self._insert_docm(UNIV2_PAIRS, data)
        else:
            # coin is t1
            data = {
                '_id': pair_addr.lower(),
                'pindex': pindex,
                'pair': pair_addr.lower(),
                'name': f"{t1_symbol}{t0_symbol}",
                'coin_addr': t1_addr.lower(),
                'coin_symbol': t1_symbol,
                'coin_decimal': t1_decimal,
                'stable_addr': t0_addr.lower(),
                'stable_symbol': t0_symbol,
                'stable_decimal': t0_decimal
            }
            self._insert_docm(UNIV2_PAIRS, data)

    def _insert_docm(self, coll: str, data):
        try:
            self.db[coll].insert_one(data)
        except Exception as e:
            lg.error(e)

    async def _fetch_erc20(self, addr: str) -> dict | None:
        ltoken = self._get_local_erc20(addr)
        if ltoken:
            lg.info(f"token is exist {ltoken['symbol']}")
            return ltoken
        else:
            lg.info(f"token is not in local:{addr} -> fetch by remote")
            rtoken = await self._get_remote_erc20(addr)
            self._to_save_erc20(rtoken)
            return rtoken

    def _to_save_erc20(self, rtoken: dict):
        if not rtoken:
            return
        lg.info(f'to save erc20 token:{rtoken["symbol"]}')
        data = {
            '_id': rtoken['address'].lower(),
            'type': 'erc20',
            'address': rtoken['address'].lower(),
            'symbol': rtoken['symbol'],
            'decimal': rtoken['decimal']
        }
        self._insert_docm(TOKENS, data)

    async def _get_remote_erc20(self, addr: str) -> dict | None:
        try:
            erc20_instance = self._gen_erc20_instance(addr)
            symbol = await getattr(erc20_instance.functions, "symbol")().call()
            decimal = await getattr(erc20_instance.functions, "decimals")().call()
            return {
                'address': addr,
                'symbol': symbol,
                'decimal': decimal
            }
        except Exception as e:
            lg.error(e)
            return None

    def _get_local_erc20(self, addr: str) -> dict | None:
        token = self.db[TOKENS].find_one(filter={'_id': addr.lower()})
        if not token:
            return None
        else:
            return {
                'address': token.get('address'),
                'symbol': token.get('symbol'),
                'decimal': token.get('decimal')
            }
        pass

    @staticmethod
    def _load_config() -> Config:
        return load_config("./config.toml")

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

    @staticmethod
    def _parse_com(log):
        address = log.get('address')
        # block_hash = log.get('blockHash')
        block_number = log.get('blockNumber')
        log_index = log.get('logIndex')
        topics = log.get('topics')
        tx_hash = log.get('transactionHash')
        tx_index = log.get('transactionIndex')
        return {
            '_id': f"N{block_number}I{log_index}",
            'address': address.lower(),
            'block_number': block_number,
            # 'block_hash': block_hash.hex().lower(),# 废弃字段
            'log_index': log_index,
            'tx_hash': tx_hash.hex().lower(),
            'tx_index': tx_index,
            'topic0': [a.hex() for a in topics]
        }

    # 处理factory的合约event
    def _handle_factory_event(self, ts: int, from_: str, to: str, log):
        topics = log.get('topics')
        if not topics:
            return
        match topics[0].hex().lower():
            case '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9':
                event_name = "PairCreated"
                lg.info(f"find event {event_name}")
                self._handle_factory_event_paircreated(ts, from_, to, log, event_name)

    def _handle_factory_event_paircreated(self, ts: int, from_: str, to: str, log, event_name):
        print(log)
        event = self._parse_com(log)
        print(event)
        arg_types = ['address', 'uint256']
        data = log.get('data')
        print(data)
        topics = log.get("topics")
        token0 = topics[1].hex().replace("000000000000000000000000", "")
        token1 = topics[2].hex().replace("000000000000000000000000", "")
        (pair, pindex) = abi.decode(arg_types, data)
        entity = {
            'token0': token0.lower(),
            'token1': token1.lower(),
            'pair': pair.lower(),
            'pindex': pindex
        }
        event['from'] = from_
        event['to'] = to
        event['name'] = event_name
        event['ts'] = ts
        event['entity'] = entity
        self._save_factory_paircreated(event)

    def _save_factory_paircreated(self, event: dict):
        try:
            self.db[UNIV2_EVENT].insert_one(event)
        except Exception as e:
            lg.error(e)

    # 处理pair合约的event
    def _handle_pair_event(self, ts, from_, log):
        # todo
        pass


async def task():
    lg.info("start to sync ... ...")
    await Task().debug()
    # await Task().run()

# 0x406df6e4f04d337e323b7710c6a6dfea34b6967177b31175c2909efdfd83b32f
# 0x406df6e4f04d337e323b7710c6a6dfea34b6967177b31175c2909efdfd83b32f
