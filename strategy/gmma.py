'''
顾比线，https://zhuanlan.zhihu.com/p/38365661
'''

from common import utils
import numpy as np
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


'''
GMMA顾比线，用多条长短均线分析
'''
def signal_indicator(df, para=[2, 10, 0.1]):
    """
    短期均线组：3、5、8、10、12、15。

    长期均线组：30、35、40、45、50、60。
    """

    # ===计算指标
    n = para[0] #短均线间隔
    m = para[1] #长均线间隔
    sb= para[2] #短线起始位
    lb = para[3] #长线起始位
    # 计算均线
    df['mean_short_3'] = df['close'].rolling(sb+n, min_periods=1).mean() #n日的均值
    df['mean_short_5'] = df['close'].rolling(sb+2*n, min_periods=1).mean()  # n日的均值
    df['mean_short_8'] = df['close'].rolling(sb+3*n, min_periods=1).mean()  # n日的均值
    df['mean_short_10'] = df['close'].rolling(sb+4*n, min_periods=1).mean()  # n日的均值
    df['mean_short_12'] = df['close'].rolling(sb+5*n, min_periods=1).mean()  # n日的均值
    df['mean_short_15'] = df['close'].rolling(sb+6*n, min_periods=1).mean()  # n日的均值

    df['mean_long_30'] = df['close'].rolling(lb+m, min_periods=1).mean()  # n日的均值
    df['mean_long_35'] = df['close'].rolling(lb+2*m, min_periods=1).mean()  # n日的均值
    df['mean_long_40'] = df['close'].rolling(lb+3*m, min_periods=1).mean()  # n日的均值
    df['mean_long_45'] = df['close'].rolling(lb+4*m, min_periods=1).mean()  # n日的均值
    df['mean_long_50'] = df['close'].rolling(lb+5*m, min_periods=1).mean()  # n日的均值
    df['mean_long_60'] = df['close'].rolling(lb+5*m, min_periods=1).mean()  # n日的均值


    # ===找出做多信号
    # 短线组向上穿越长线组
    condition1 = df['bbPb'] > (1-th) # 当前K线的收盘价 > %b线的0.6,  0.5为中线
    condition2 = df['bbPb'].shift(1) <= (1-th)  # 前一刻K线的收盘价 <= （中线+偏移）

    df.loc[condition1 & condition2 , 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # ===找出做多平仓信号
    condition1 = df['bbPb'] < 0.5
    condition2 = df['bbPb'].shift(1) >= 0.5
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # ===找出做空信号
    condition1 = df['bbPb'] < (0+th)
    condition2 = df['bbPb'].shift(1) >= (0+th)
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # ===找出做空平仓信号
    condition1 = df['bbPb'] > 0.5
    condition2 = df['bbPb'].shift(1) <= 0.5
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # ===合并做多做空信号，去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)  # 若pandas版本是最新的，请使用本行代码代替上面一行

    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']
    df.drop(['median', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # ===由signal计算出实际的每天持有仓位
    # signal的计算运用了收盘价，是每根K线收盘之后产生的信号，到第二根开盘的时候才买入，仓位才会改变。
    df['pos'] = df['signal'].shift()
    df['pos'].fillna(method='ffill', inplace=True)
    df['pos'].fillna(value=0, inplace=True)  # 将初始行数的position补全为0

    return df
