from datetime import datetime, timedelta
import time
from time import sleep
import pandas as pd
from common import utils
from common.utils import log_exp

pd.set_option('display.max_rows', 1000)


def get_candle_data(exchange, symbol, time_interval='1m', is_contract =False):
    """
    # 直接获取k线数据, 私有方法
    """
    para = dict()
    if is_contract and exchange.name == 'Okex':
        para = {'contract_type': 'quarter'}
    # 抓取k线
    loop_count = 0
    while True:
        try:
            loop_count +=1
            content = None
            if exchange.name == 'OKEX':
                # 抓取数据 如果是获取合约数据则加上params={'contract_type': 'quarter'}
                content = exchange.fetch_ohlcv(symbol, timeframe=time_interval, since=0, params=para)  # 这里有个since=0的问题，是okex特有的，在其他交易所得用limit
            elif exchange.name =='Bitfinex v2':
                # bitfinex V2拿数据 v1处理资产
                content = exchange.fetch_ohlcv(symbol, timeframe=time_interval, limit=1000, since=None)
            else:
                log_exp.error('错误的交易所，exchage.name %s', exchange.name)
                exit(110)
            # 整理数据
            df = pd.DataFrame(content, dtype=float)
            df.rename(columns={0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}, inplace=True)
            df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')
            df['candle_begin_time_GMT8'] = df['candle_begin_time'] + timedelta(hours=8)
            df = df[['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']]

            return df
        except Exception as e:
            if loop_count>=5 :
                break
            log_exp.error('下载数据报错,10秒后重试%s', e)
            time.sleep(20)


'''
# 把当前时刻的前一时刻前的数据get到，
'''
def update_kline(exchange,symbol,interval_time,next_run_time,detect_time=0):
    #默认无间隔检测，当时间接近时需要加快请求
    i = 0 #重试次数
    while i<6:
        i+=1
        log_exp.debug('next data time(%s): %s', str(i), next_run_time)
        k_data = get_candle_data(exchange, symbol,interval_time,False)

        #logger.debug('获取的kline最后一行(%s)：\n%s',datetime.now().strftime("%Y-%m-%d %H:%M:%S"),k_data.tail(1))
        # 判断是否包含最新的数据
        _temp = k_data[k_data['candle_begin_time_GMT8'] == (next_run_time - utils.time_span(interval_time))]
        next_temp = k_data[k_data['candle_begin_time_GMT8'] == next_run_time]
        if detect_time == 0:#请求数据模式
                if _temp.empty:#前一刻数据存在
                    #logger.debug('获取数据不包含最新的数据，重新获取')
                    sleep(20)
                    continue
                else:
                    log_exp.debug('直接返回最新数据，tail(1)\n%s', _temp)
                    return k_data
        else:#检测数据模式
            if next_temp.empty:#当前时刻数据存在
                sleep(detect_time)
                continue
            else:
                log_exp.debug('侦测到最新数据并返回，tail(1)\n%s', next_temp)
                return k_data