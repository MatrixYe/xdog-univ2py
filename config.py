# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------
import toml
from pydantic import BaseModel, HttpUrl


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


class Config(BaseModel):
    title: str
    network: str
    factory: str
    weth: str
    full_pair: bool

    node_url: HttpUrl
    start_block: int
    sync_interval: int

    mongo: MongoConfig
    redis: RedisConfig


def load_config(file_path: str) -> Config:
    f = toml.load(file_path)
    c = Config.parse_obj(f)
    return c
