# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         a 
# Author:       yepeng
# Date:         2021/10/22 2:44 下午
# Description: 
# -------------------------------------------------------------------------------

import utils

mg = utils.connect_mongo(host='127.0.0.1', port=5004, username="root", password="password", db="ethereum")


def run():
    print('this is task 1')
    base = mg['univ2_base'].find_one({'_id': 1})
    print(base)
