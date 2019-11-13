

from datetime import timedelta, datetime
from time import sleep

import pandas as pd
from common import utils

from common.utils import log_exp
from common import k_lines
import copy
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
        log_exp.info('program is runing now !')
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
            log_exp.error('当前时间(%s)超过了下次运行时间(%s)，请检查。程序立刻执行数据更新', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.next_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.k_data = k_lines.update_kline(self.exchange, self.symbol, self.interval_time, self.next_time)
        else:
            if ((self.next_time - datetime.now())< timedelta(seconds=60)):
                #差60s就到达下一个运行时间，直接检测执行
                log_exp.debug('马上到点，启动高频检测数据[间隔50s]')
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
            log_exp.debug('df_signal tail(3): \n %s', df_signal.tail(3))
            signal = df_signal.iloc[-1]['signal']  # 最新数据的那个信号
            signal_before = df_signal.iloc[-1]['pos']  # 前一刻的持仓
            log_exp.info('当前最新数据时间 %s', self.next_time)
            log_exp.info('当前交易信号为:%s', signal)
            log_exp.info('前一刻理论持仓为:%s', signal_before)
            #调试代码
            # signal = 1
            # signal_before = 0
            if not pd.isna(signal):
                # self.operation_para =>【order_para=[multi, percent, my_exchange.bitfinex_instance()]】
                # 根据1日线决定倍率
                k_data_1day = k_lines.get_candle_data(self.exchange, self.symbol, '1d')
                diff_percent = 0 # 当前与均值的差异
                if k_data_1day is None:
                    ratio = 1
                else:
                    # 计算30日均线
                    k_data_1day['median'] = k_data_1day['close'].rolling(30, min_periods=1).mean()  # n日的均值
                    close_cur = df_signal.iloc[-1]['close']  # 最新数据的那个信号
                    mean_cur = k_data_1day.iloc[-1]['median']
                    mean_max = max(list(map(lambda x: abs(x), k_data_1day['median'].values.tolist())))
                    diff_percent = (close_cur - mean_cur)/mean_cur  # 正负都有可能
                    max_diff_percent = (mean_max - mean_cur)/mean_cur  # 为正数
                    # 分成5个等级：1，1.5，2，2.5，3
                    mean_percent = max_diff_percent/5
                    diff_percent_abs = abs(diff_percent)
                    if 0 <= diff_percent_abs < mean_percent:
                        ratio = 1
                    elif mean_percent <= diff_percent_abs < mean_percent*2:
                        ratio = 1.5
                    elif mean_percent*2 <= diff_percent_abs < mean_percent*3:
                        ratio = 2
                    elif mean_percent*3 <= diff_percent_abs < mean_percent*4:
                        ratio = 2.5
                    elif mean_percent*4 <= diff_percent_abs:
                        ratio = 3
                    else:
                        ratio = 1
                operation_para_modify = copy.copy(self.operation_para)  # 操作副本
                # 0 表示自动。 均值上方且做多信号； 均值下方且做空信号；
                if self.operation_para[0] == 0 and ((diff_percent > 0 and signal == 1) or (diff_percent < 0 and signal == -1)):
                    operation_para_modify[0] = ratio
                else:
                    operation_para_modify[0] = 1

                    log_exp.info('%d倍持仓！')
                # 具体参数，需要结合对应函数给相应参数
                self.trading_operation(self.exchange, self.symbol, signal, signal_before, operation_para_modify)
            log_exp.debug('----------group line-------------')
