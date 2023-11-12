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

    node_url: HttpUrl
    start_block: int
    sync_interval: int
    sync_range: int

    reparse: bool
    parse_range: int
    parse_interval: int

    mongo: MongoConfig
    redis: RedisConfig


def load_config(file_path: str) -> Config:
    c = Config.parse_obj(toml.load(file_path))
    print(c)
    return c
