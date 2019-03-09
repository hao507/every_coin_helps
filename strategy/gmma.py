'''
顾比线，https://zhuanlan.zhihu.com/p/38365661
'''

from common import utils
import numpy as np
import pandas as pd
import talib
from common import indicators
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


'''
GMMA顾比线，用多条长短均线分析
'''
def signal_indicator(df, para=[3, 30, 3, 5]):
    """
    短期均线组：3、5、8、10、12、15。

    长期均线组：30、35、40、45、50、60。
    """

    # ===计算指标
    sb= para[0] #短线起始位
    lb = para[1] #长线起始位
    n = para[2]  # 短均线间隔
    m = para[3]  # 长均线间隔

    # 计算均线
    df['mean_short_3'] = df['close'].rolling(sb, min_periods=1).mean() #n日的均值
    df['mean_short_5'] = df['close'].rolling(sb+1*n, min_periods=1).mean()  # n日的均值
    df['mean_short_8'] = df['close'].rolling(sb+2*n, min_periods=1).mean()  # n日的均值
    df['mean_short_10'] = df['close'].rolling(sb+3*n, min_periods=1).mean()  # n日的均值
    df['mean_short_12'] = df['close'].rolling(sb+4*n, min_periods=1).mean()  # n日的均值
    df['mean_short_15'] = df['close'].rolling(sb+5*n, min_periods=1).mean()  # n日的均值

    df['mean_long_30'] = df['close'].rolling(lb, min_periods=1).mean()  # n日的均值
    df['mean_long_35'] = df['close'].rolling(lb+1*m, min_periods=1).mean()  # n日的均值
    df['mean_long_40'] = df['close'].rolling(lb+2*m, min_periods=1).mean()  # n日的均值
    df['mean_long_45'] = df['close'].rolling(lb+3*m, min_periods=1).mean()  # n日的均值
    df['mean_long_50'] = df['close'].rolling(lb+4*m, min_periods=1).mean()  # n日的均值
    df['mean_long_60'] = df['close'].rolling(lb+5*m, min_periods=1).mean()  # n日的均值


    def apply_calcute(x):
        '''
        计算顾比线穿越的情况
        :param x:
        :return:
        '''
        short_min = min(x['mean_short_3'],x['mean_short_5'],x['mean_short_8'],x['mean_short_10'],x['mean_short_12'],x['mean_short_15'])
        long_max = max(x['mean_long_30'],x['mean_long_35'],x['mean_long_40'],x['mean_long_45'],x['mean_long_50'],x['mean_long_60'])

        short_max = max(x['mean_short_3'], x['mean_short_5'], x['mean_short_8'], x['mean_short_10'], x['mean_short_12'], x['mean_short_15'])
        long_min = min(x['mean_long_30'], x['mean_long_35'], x['mean_long_40'], x['mean_long_45'], x['mean_long_50'], x['mean_long_60'])
        if short_min > long_max:#短线都在上方
            return 1
        if short_max < long_min:#短线都在下方
            return -1
        else:
            return 0

    df['signal'] = df.apply(apply_calcute, axis=1)

    #去除为nan的信号后，只保留相邻信号且相异，其他置为nan
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']
    #移除多余的临时数据
    df.drop(['mean_short_3', 'mean_short_5', 'mean_short_8', 'mean_short_10', 'mean_short_12', 'mean_short_15',
             'mean_long_30','mean_long_35','mean_long_40','mean_long_45','mean_long_50','mean_long_60'], axis=1, inplace=True)
    #df['adx'] = talib.ADX(df['high'],df['low'],df['close'],timeperiod=14)
    # ===由signal计算出实际的每天持有仓位
    # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
    df['pos'] = df['signal'].shift()
    df['pos'].fillna(method='ffill', inplace=True)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

    return df
