

from datetime import timedelta, datetime
from time import sleep

import pandas as pd
from common import utils

from common.utils import logger
from common import k_lines

'''
任务启动中心
'''
class task_making:
    '''
    exchange:交易所
    func_stregy:信号分析策略
    strtegy_para:信号策略参数
    '''
    def __init__(self,exchange, func_strtegy, strtegy_para,func_auto_trade,order_para, symbol ='BTC/USDT',interval_time = '5m'):

        self.exchange = exchange
        self.symbol = symbol
        self.interval_time = interval_time
        self.trading_signal = func_strtegy
        self.strtegy_para = strtegy_para
        self.trading_operation = func_auto_trade
        self.operation_para = order_para
        #初始化完就执行
        self.do_work()

    #执行外部大循环，主入口
    def do_work(self):
        logger.info('program is runing now !')
        while True:
            try:
                self.run_instance()
            except Exception as e:
                print(e)
                sleep(10)

    #检测数据
    def run_instance(self):
        #外部是大循环，dowork()会一直运行
        self.next_time = utils.next_run_time(self.interval_time)  # 得到下次运行的时间,提前2s
        self.k_data = None #每次都需要初始化为nan

        #数据获取方式优化
        if self.next_time < datetime.now():
            #下个运行时刻不知什么原因错过了
            logger.error('当前时间(%s)超过了下次运行时间(%s)，请检查。程序立刻执行数据更新',datetime.now().strftime("%Y-%m-%d %H:%M:%S"),self.next_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.k_data = k_lines.update_kline(self.exchange, self.symbol, self.interval_time, self.next_time)
        else:
            if ((self.next_time - datetime.now())< timedelta(seconds=60)):
                #差60s就到达下一个运行时间，直接检测执行
                logger.debug('马上到点，启动高频检测数据[间隔50s]')
                self.k_data = k_lines.update_kline(self.exchange, self.symbol, self.interval_time, self.next_time,detect_time=50)
            else:
                #选择sleep方式，而非不断循环执行
                sleep(((self.next_time - datetime.now())*0.7).seconds)

        # self.k_data = utils.file_obj_convert()#调试代码
        # self.k_data = self.k_data[0:960]#调试代码
        if self.k_data is not None:
            self.k_data = self.k_data[self.k_data['candle_begin_time_GMT8'] < pd.to_datetime(self.next_time)]  # 去除target_time周期的数据
            #logger.debug('k_data tail(3): \n %s', self.k_data.tail(3))
            #拿到时刻数据，进行信号分析
            df_signal = self.trading_signal(self.k_data,self.strtegy_para)
            logger.debug('df_signal tail(3): \n %s',df_signal.tail(3))
            signal = df_signal.iloc[-1]['signal']  # 最新数据的那个信号
            signal_before = df_signal.iloc[-1]['pos']  # 前一刻的持仓
            logger.info('当前最新数据时间 %s', self.next_time)
            logger.info('当前交易信号为:%s', signal)
            logger.info('前一刻理论持仓为:%s', signal_before)
            #调试代码
            # signal=1
            # signal_before=0
            if not pd.isna(signal):
                #具体参数，需要结合对应函数给相应参数
                self.trading_operation(self.exchange,self.symbol,signal,signal_before,self.operation_para)
            logger.debug('----------group line-------------')
#
#
# if __name__== '__main__':
#     task_making(
#                 my_exchange.bitfinexV2_instance(),
#                 bulin.signal_bolling,strtegy_para=[370, 3.5],
#                 func_auto_trade=orders.auto_trade_leverage, order_para=[1.5, 0.1, my_exchange.bitfinex_instance()],
#                 symbol ='BTC/USDT',
#                 interval_time = '5m'
#                 )