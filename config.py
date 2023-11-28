# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import toml
from pydantic import BaseModel, HttpUrl


# title = "uniswap v2 sync&parse"
#
# [network]
# name = "ethereum"
# interval = 10
#
# [sync]
# factory = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"
# weth = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
# start_block = 0
# interval = 7
# range = 400
# node_url = "https://indulgent-rough-feather.discover.quiknode.pro/30e19cc5162c0caa6c91678c457b0b166b09cc69/"
# full_pair = false
# history_enable = true
#
# [parse]
# reparse = false
# parse_range = 500
# parse_interval = 3
#
# [mongo]
# host = "localhost"
# port = 5004
# username = "root"
# password = "password"
#
# [redis]
# host = "localhost"
# port = 5005
# password = "password"
# db = 0

class MongoConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str


class RedisConfig(BaseModel):
    host: str
    port: int
    password: str
    db: int


class Sync(BaseModel):
    factory: str
    weth: str
    full_pair: bool
    node_url: HttpUrl
    start_block: int
    sync_interval: int
    sync_range: int


class Config(BaseModel):
    title: str
    network: str

    reparse: bool
    parse_range: int
    parse_interval: int

    mongo: MongoConfig
    redis: RedisConfig


def load_config(file_path: str) -> Config:
    c = Config.parse_obj(toml.load(file_path))
    return c
