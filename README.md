# xdog univ2 数据同步器

## 功能

1. 提供full-pair模式，支持同步全部池子基本数据
2. 步进1进行扫描区块，同步uniswap v2相关数据，并解析

## 安装条件

- python = 3.10.13
- mongodb 数据库
- redis 数据库

配置文件为``config.toml`

## 启动

`cd xdog-univ2py` 进入工程目录

- `make sync` 开启新终端，启动数据同步器
- `make pnl` 开启新终端，启动盈利统计任务

