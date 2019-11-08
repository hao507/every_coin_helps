#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   dao.py 
@Desciption    :   基础配置链接
@Author    :   LensonYuan   
@Contact :   15000959076@163.com
@License :   (C)Copyright 2019-2021, HQ-33Lab

@Modify Time         @Version   
------------         --------
2019/11/8 10:45         1.0  
"""
from datacache.db_io_lite import SQLITE

sqlite_cache = SQLITE('data.db')

# 创建存储数据表
sqlite_cache.ExecNonQuery("create table if not exists history_cache( id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, record_type char(10) , trade_signal char(8), trade_multiple char(8), trade_amount char(8), trade_profit char(8), trade_profit_percent char(8), account char(10), update_time TIMESTAMP NOT NULL DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime')) )")
# ON UPDATE (datetime(CURRENT_TIMESTAMP,'localtime')) #无效
# 示例数据
# sqlite_cache.ExecNonQuery("INSERT INTO history_cache(record_type, trade_signal, trade_multiple, trade_amount, account) VALUES('交易\查询', '做空/做多/平仓', '3', '80', '100')")
# xx = sqlite_cache.ExecQuery('select * from history_cache')
# print(xx)